from guard import AUDIT_LOG, handle_request


def setup_function():
    AUDIT_LOG.clear()


def test_authorized_balance_request_is_allowed_and_audited():
    result = handle_request({
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    })

    assert result["allowed"] is True
    assert result["result"]["balance"] == 25000.0
    assert len(AUDIT_LOG) == 1
    assert AUDIT_LOG[0]["allowed"] is True


def test_unauthorized_balance_request_is_blocked_and_audited():
    result = handle_request({
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-2001"},
    })

    assert result["allowed"] is False
    assert result["reason"] == "User not authorized for account"
    assert len(AUDIT_LOG) == 1
    assert AUDIT_LOG[0]["allowed"] is False