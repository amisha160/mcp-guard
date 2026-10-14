import json
import os
import subprocess
import sys
from pathlib import Path

from guard import AUDIT_LOG, audit, load_audit_log


def test_load_audit_log_skips_malformed_lines_and_non_objects(tmp_path):
    log = tmp_path / "audit.jsonl"
    expected = {"user_id": "riya", "tool": "get_balance", "allowed": True}
    log.write_text(
        json.dumps(expected) + "\n"
        "{malformed json}\n"
        "42\n"
        '["not", "an", "object"]\n',
        encoding="utf-8",
    )

    assert load_audit_log(_log_path=str(log)) == [expected]


def test_load_audit_log_missing_file_returns_empty_list(tmp_path):
    assert load_audit_log(_log_path=str(tmp_path / "missing.jsonl")) == []


def test_audit_log_loads_on_module_startup(tmp_path):
    log = tmp_path / "startup-audit.jsonl"
    log.write_text(
        json.dumps({"tool": "previous_event", "allowed": True}) + "\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["MCP_GUARD_AUDIT_LOG"] = str(log)
    env["MCP_GUARD_SECURITY_ALERTS_LOG"] = str(tmp_path / "alerts.jsonl")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import guard; "
            "assert any(e.get('tool') == 'previous_event' "
            "for e in guard.AUDIT_LOG); print('startup reload passed')",
        ],
        cwd=str(Path.cwd()),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "startup reload passed" in result.stdout


def test_audit_write_failure_does_not_crash_or_change_authorization(tmp_path):
    before = len(AUDIT_LOG)
    impossible_path = tmp_path / "missing-directory" / "audit.jsonl"

    audit("riya", "get_balance", True, "Allowed", _log_path=str(impossible_path))

    assert len(AUDIT_LOG) == before + 1
    assert AUDIT_LOG[-1]["allowed"] is True

def test_handle_request_authorization_is_unchanged_when_audit_write_fails(
    tmp_path, monkeypatch
):
    import guard

    impossible_path = tmp_path / "missing-directory" / "audit.jsonl"
    monkeypatch.setattr(guard, "AUDIT_LOG_PATH", str(impossible_path))

    request = {
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    }

    result = guard.handle_request(request)

    # A logging failure must not turn an authorized request into a denial.
    assert result["allowed"] is True

