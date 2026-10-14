import guard


def test_balance_response_includes_low_risk():
    result = guard.handle_request({
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    })

    assert result["allowed"] is True
    assert result["risk"]["level"] == "low"
    assert result["risk"]["score"] == 5


def test_transfer_response_includes_risk_and_waits_for_approval():
    result = guard.handle_request({
        "user_id": "riya",
        "tool": "transfer",
        "arguments": {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": 100,
        },
    })

    assert result["allowed"] is True
    assert result["status"] == "pending_approval"
    assert result["risk"]["level"] == "medium"
    assert result["risk"]["score"] == 40
    assert result["approval_id"] in guard.PENDING_APPROVALS


def test_high_risk_transfer_creates_security_alert():
    before = len(guard.SECURITY_ALERTS)

    result = guard.handle_request({
        "user_id": "riya",
        "tool": "transfer",
        "arguments": {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": 10001,
        },
    })

    # Existing validation must reject an amount above the limit.
    assert result["allowed"] is False
    assert len(guard.SECURITY_ALERTS) > before
