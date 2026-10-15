"""
audit_integrity.py — Append-only audit log with a SHA-256 hash chain.

Every audit record is hashed together with the previous record's hash,
forming a chain.  Tampering with, deleting, or reordering any entry breaks
all subsequent hashes and is detected by verify().

Security disclaimer
-------------------
A local hash chain does NOT prevent an attacker who controls both the audit
file and this module's source from rewriting the entire history and
recomputing a valid chain.  This mechanism detects accidental corruption and
opportunistic tampering, not a determined adversary with full system access.
For stronger guarantees, ship logs to an independent append-only store
(e.g. a remote syslog sink or a transparency log service).

⚠ SIMULATION — no real financial data is stored or transmitted.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any

import config

# ── Module-level state ─────────────────────────────────────────────────────────
_write_lock = threading.Lock()   # serialise concurrent appends

# Sentinel for the genesis (first) record.
GENESIS_PREV_HASH = "0" * 64


# ── Hashing ────────────────────────────────────────────────────────────────────

def _hash_entry(prev_hash: str, record: dict[str, Any]) -> str:
    """
    Compute SHA-256( prev_hash || canonical_json(record) ).

    The record dict must NOT contain the 'hash' or 'prev_hash' keys when
    this function is called — they are added afterwards.
    """
    payload = prev_hash + json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ── Reading ────────────────────────────────────────────────────────────────────

def _read_raw(path: str) -> list[dict[str, Any]]:
    """Return all valid JSON lines from the integrity log, ignoring blanks."""
    records: list[dict[str, Any]] = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return records


def get_last_hash(path: str | None = None) -> str:
    """Return the hash of the most recently written record, or the genesis hash."""
    path = path or config.AUDIT_INTEGRITY_PATH
    records = _read_raw(path)
    if records:
        return records[-1].get("hash", GENESIS_PREV_HASH)
    return GENESIS_PREV_HASH


# ── Writing ────────────────────────────────────────────────────────────────────

def append(record: dict[str, Any], path: str | None = None) -> str:
    """
    Append *record* to the integrity-protected audit log.

    The function is thread-safe (module-level lock).  It computes the hash
    chain, writes a single JSON line, and returns the new hash.

    The caller must NOT include 'hash' or 'prev_hash' in *record*; they are
    injected here.  A shallow copy is made so the caller's dict is unchanged.

    Parameters
    ----------
    record  : Audit event dict (already serialisable to JSON).
    path    : Override for the integrity log path.

    Returns
    -------
    str — The SHA-256 hash of the newly appended record.
    """
    path = path or config.AUDIT_INTEGRITY_PATH

    # Strip any accidental hash fields before computing
    clean = {k: v for k, v in record.items() if k not in ("hash", "prev_hash")}

    with _write_lock:
        prev = get_last_hash(path)
        entry_hash = _hash_entry(prev, clean)
        stored = {**clean, "prev_hash": prev, "hash": entry_hash}

        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(stored, separators=(",", ":")) + "\n")
                fh.flush()
        except Exception:
            # Integrity-log write failures must not crash the guard.
            pass

    return entry_hash


# ── Verification ───────────────────────────────────────────────────────────────

class IntegrityError(Exception):
    """Raised when the hash chain is broken."""


def verify(path: str | None = None) -> dict[str, Any]:
    """
    Verify the entire hash chain.

    Returns a summary dict:
    {
        "ok":           bool,
        "records":      int,       # total records checked
        "broken_at":    int|None,  # 0-based index of first broken record
        "error":        str|None,  # human-readable description
        "last_hash":    str,
    }

    Does NOT raise an exception — callers inspect the "ok" field.
    """
    path = path or config.AUDIT_INTEGRITY_PATH
    records = _read_raw(path)

    if not records:
        return {
            "ok": True,
            "records": 0,
            "broken_at": None,
            "error": None,
            "last_hash": GENESIS_PREV_HASH,
        }

    prev = GENESIS_PREV_HASH
    for i, rec in enumerate(records):
        stored_hash = rec.get("hash", "")
        stored_prev = rec.get("prev_hash", "")

        # Check the prev_hash link
        if stored_prev != prev:
            return {
                "ok": False,
                "records": len(records),
                "broken_at": i,
                "error": (
                    f"Record {i}: prev_hash mismatch "
                    f"(expected {prev!r}, got {stored_prev!r})"
                ),
                "last_hash": stored_hash,
            }

        # Recompute hash over the core fields (excluding hash + prev_hash)
        clean = {k: v for k, v in rec.items() if k not in ("hash", "prev_hash")}
        expected = _hash_entry(prev, clean)

        if stored_hash != expected:
            return {
                "ok": False,
                "records": len(records),
                "broken_at": i,
                "error": (
                    f"Record {i}: hash mismatch "
                    f"(expected {expected!r}, got {stored_hash!r})"
                ),
                "last_hash": stored_hash,
            }

        prev = stored_hash

    return {
        "ok": True,
        "records": len(records),
        "broken_at": None,
        "error": None,
        "last_hash": prev,
    }


# ── CLI utility ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    log_path = sys.argv[1] if len(sys.argv) > 1 else config.AUDIT_INTEGRITY_PATH
    result = verify(log_path)
    status = "PASS" if result["ok"] else "FAIL"
    print(f"[{status}] {result['records']} records — {log_path}")
    if not result["ok"]:
        print(f"  ✗ {result['error']}")
        sys.exit(1)
    print(f"  last_hash={result['last_hash'][:16]}...")
