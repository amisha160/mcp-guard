import importlib
import json

import guard


def test_alert_is_persisted_and_can_be_reloaded(tmp_path):
    alert_path = tmp_path / "alerts.jsonl"
    alert = {
        "time": "2026-01-01T00:00:00+00:00",
        "user_id": "test-user",
        "tool": "transfer",
        "allowed": False,
        "reason": "Test security alert",
    }

    guard.record_security_alert(alert, _log_path=str(alert_path))

    saved = json.loads(alert_path.read_text(encoding="utf-8").strip())
    assert saved == alert
    assert guard.load_security_alerts(_log_path=str(alert_path)) == [alert]


def test_loader_skips_malformed_lines(tmp_path):
    alert_path = tmp_path / "alerts.jsonl"
    valid = {
        "time": "2026-01-01T00:00:00+00:00",
        "user_id": "test-user",
        "tool": "transfer",
        "allowed": False,
        "reason": "Valid alert",
    }
    alert_path.write_text(
        json.dumps(valid) + "\n" + "{broken json\n" + "[]\n",
        encoding="utf-8",
    )

    assert guard.load_security_alerts(_log_path=str(alert_path)) == [valid]


def test_module_startup_loads_existing_alerts(tmp_path):
    import os
    import subprocess
    import sys

    alert_path = tmp_path / "alerts.jsonl"
    alert = {
        "time": "2026-01-01T00:00:00+00:00",
        "user_id": "restart-user",
        "tool": "transfer",
        "allowed": False,
        "reason": "Previously saved alert",
    }
    alert_path.write_text(json.dumps(alert) + "\n", encoding="utf-8")

    env = os.environ.copy()
    env["MCP_GUARD_SECURITY_ALERTS_LOG"] = str(alert_path)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, guard; print(json.dumps(guard.SECURITY_ALERTS))",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )

    assert alert in json.loads(result.stdout)
