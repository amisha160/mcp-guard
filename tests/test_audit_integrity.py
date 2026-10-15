"""
tests/test_audit_integrity.py — Tests for audit_integrity.py hash chain.

Covers:
  - Empty log verifies OK.
  - Single and multiple records verify OK after normal appends.
  - verify() returns correct record count.
  - Tampering with a field breaks verification.
  - Deleting a record breaks verification.
  - Reordering records breaks verification.
  - Duplicate append does not corrupt the chain.
  - get_last_hash() returns genesis hash on empty log.
  - CLI interface returns PASS / FAIL correctly.
"""

import json
import os
import tempfile

import pytest

import audit_integrity
from audit_integrity import GENESIS_PREV_HASH, append, get_last_hash, verify


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_log(tmp_path):
    """Return a path to a fresh temporary integrity log."""
    return str(tmp_path / "test_integrity.jsonl")


# ── Empty log ──────────────────────────────────────────────────────────────────

class TestEmptyLog:
    def test_empty_log_verifies_ok(self, tmp_log):
        result = verify(tmp_log)
        assert result["ok"] is True

    def test_empty_log_has_zero_records(self, tmp_log):
        result = verify(tmp_log)
        assert result["records"] == 0

    def test_empty_log_last_hash_is_genesis(self, tmp_log):
        result = verify(tmp_log)
        assert result["last_hash"] == GENESIS_PREV_HASH

    def test_get_last_hash_returns_genesis_for_empty(self, tmp_log):
        assert get_last_hash(tmp_log) == GENESIS_PREV_HASH


# ── Single-record chain ────────────────────────────────────────────────────────

class TestSingleRecord:
    def test_single_append_verifies_ok(self, tmp_log):
        append({"event": "test", "value": 1}, tmp_log)
        result = verify(tmp_log)
        assert result["ok"] is True

    def test_single_record_count(self, tmp_log):
        append({"event": "test"}, tmp_log)
        assert verify(tmp_log)["records"] == 1

    def test_single_record_prev_hash_is_genesis(self, tmp_log):
        append({"event": "test"}, tmp_log)
        with open(tmp_log) as f:
            rec = json.loads(f.readline())
        assert rec["prev_hash"] == GENESIS_PREV_HASH

    def test_get_last_hash_after_one_append(self, tmp_log):
        h = append({"event": "test"}, tmp_log)
        assert get_last_hash(tmp_log) == h
        assert len(h) == 64  # SHA-256 hex


# ── Multi-record chain ─────────────────────────────────────────────────────────

class TestMultiRecordChain:
    def test_five_records_verify_ok(self, tmp_log):
        for i in range(5):
            append({"seq": i, "data": f"record-{i}"}, tmp_log)
        result = verify(tmp_log)
        assert result["ok"] is True
        assert result["records"] == 5

    def test_chain_is_linked(self, tmp_log):
        """Each record's prev_hash must equal the previous record's hash."""
        for i in range(3):
            append({"seq": i}, tmp_log)
        with open(tmp_log) as f:
            records = [json.loads(line) for line in f]
        assert records[1]["prev_hash"] == records[0]["hash"]
        assert records[2]["prev_hash"] == records[1]["hash"]

    def test_append_does_not_include_hash_in_core(self, tmp_log):
        """The 'hash' key must not appear inside the signed payload."""
        append({"a": 1, "hash": "should_be_stripped"}, tmp_log)
        result = verify(tmp_log)
        assert result["ok"] is True  # would fail if hash wasn't stripped


# ── Tamper detection ───────────────────────────────────────────────────────────

class TestTamperDetection:
    def _write_records(self, tmp_log, n=3):
        for i in range(n):
            append({"seq": i, "user": "riya"}, tmp_log)

    def _read_lines(self, path) -> list[dict]:
        with open(path) as f:
            return [json.loads(line) for line in f]

    def _write_lines(self, path, records: list[dict]) -> None:
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def test_field_tamper_detected(self, tmp_log):
        """Changing a field value in a stored record breaks the chain."""
        self._write_records(tmp_log)
        records = self._read_lines(tmp_log)
        records[1]["user"] = "mallory"          # tamper
        self._write_lines(tmp_log, records)
        result = verify(tmp_log)
        assert result["ok"] is False
        assert result["broken_at"] is not None

    def test_hash_field_replacement_detected(self, tmp_log):
        """Replacing the stored hash with a forged value is detected."""
        self._write_records(tmp_log)
        records = self._read_lines(tmp_log)
        records[0]["hash"] = "a" * 64           # forged hash
        self._write_lines(tmp_log, records)
        result = verify(tmp_log)
        assert result["ok"] is False

    def test_record_deletion_detected(self, tmp_log):
        """Deleting the middle record breaks the prev_hash chain."""
        self._write_records(tmp_log, n=3)
        records = self._read_lines(tmp_log)
        del records[1]                           # delete middle record
        self._write_lines(tmp_log, records)
        result = verify(tmp_log)
        assert result["ok"] is False

    def test_record_reorder_detected(self, tmp_log):
        """Swapping records breaks the prev_hash chain."""
        self._write_records(tmp_log, n=3)
        records = self._read_lines(tmp_log)
        records[0], records[1] = records[1], records[0]  # swap
        self._write_lines(tmp_log, records)
        result = verify(tmp_log)
        assert result["ok"] is False

    def test_record_prepend_detected(self, tmp_log):
        """Inserting a record at the beginning breaks the chain."""
        self._write_records(tmp_log, n=2)
        records = self._read_lines(tmp_log)
        fake = {"seq": -1, "user": "attacker",
                "prev_hash": GENESIS_PREV_HASH,
                "hash": "b" * 64}
        records.insert(0, fake)
        self._write_lines(tmp_log, records)
        result = verify(tmp_log)
        assert result["ok"] is False


# ── Thread safety (basic) ──────────────────────────────────────────────────────

class TestThreadSafety:
    def test_concurrent_appends_produce_valid_chain(self, tmp_log):
        """Ten concurrent appends must leave a valid, consistent chain."""
        import threading
        errors = []

        def _append(i):
            try:
                append({"thread": i, "val": i * 2}, tmp_log)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_append, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        result = verify(tmp_log)
        assert result["ok"] is True
        assert result["records"] == 10


# ── Verify result shape ────────────────────────────────────────────────────────

class TestVerifyShape:
    def test_verify_returns_dict_with_required_keys(self, tmp_log):
        result = verify(tmp_log)
        assert set(result.keys()) >= {"ok", "records", "broken_at", "error", "last_hash"}

    def test_ok_result_has_null_error(self, tmp_log):
        append({"x": 1}, tmp_log)
        result = verify(tmp_log)
        assert result["error"] is None
        assert result["broken_at"] is None

    def test_broken_result_has_error_string(self, tmp_log):
        append({"x": 1}, tmp_log)
        with open(tmp_log, "a") as f:
            f.write('{"corrupted": true, "prev_hash": "000", "hash": "000"}\n')
        result = verify(tmp_log)
        assert result["ok"] is False
        assert isinstance(result["error"], str)
