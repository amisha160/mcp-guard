import json
import os
import subprocess
import sys


def test_audit_logs_and_security_alerts_load_together_after_restart(tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    alerts_path = tmp_path / "alerts.jsonl"

    audit_event = {
        "user_id": "restart-user",
        "tool": "get_balance",
        "allowed": True,
        "reason": "Allowed",
    }
    alert_event = {
        "user_id": "restart-user",
        "tool": "transfer",
        "allowed": False,
        "reason": "Security alert",
    }

    audit_path.write_text(json.dumps(audit_event) + "\n", encoding="utf-8")
    alerts_path.write_text(json.dumps(alert_event) + "\n", encoding="utf-8")

    env = os.environ.copy()
    env["MCP_GUARD_AUDIT_LOG"] = str(audit_path)
    env["MCP_GUARD_SECURITY_ALERTS_LOG"] = str(alerts_path)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, guard; "
            "print(json.dumps({'audit': guard.AUDIT_LOG, "
            "'alerts': guard.SECURITY_ALERTS}))",
        ],
        cwd=os.getcwd(),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    loaded = json.loads(result.stdout)
    assert audit_event in loaded["audit"]
    assert alert_event in loaded["alerts"]
