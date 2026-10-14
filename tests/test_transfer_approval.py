import pytest

import guard
from bank import get_balance


@pytest.fixture(autouse=True)
def reset_pending_approvals_and_audit():
    guard.PENDING_APPROVALS.clear()
    guard.AUDIT_LOG.clear()


def balances():
    return {
        "ACC-1001": get_balance("ACC-1001")["balance"],
        "ACC-1002": get_balance("ACC-1002")["balance"],
    }


def queue_transfer():
    before = balances()
    result = guard.handle_request(
        {
            "user_id": "riya",
            "tool": "transfer",
            "arguments": {
                "from_account": "ACC-1001",
                "to_account": "ACC-1002",
                "amount": 100,
            },
        }
    )
    return before, result


def test_transfer_waits_for_approval_without_moving_money():
    before, result = queue_transfer()

    assert result["allowed"] is True
    assert result["status"] == "pending_approval"
    assert result["approval_id"] in guard.PENDING_APPROVALS
    assert balances() == before


def test_authorized_approver_executes_transfer_once():
    before, result = queue_transfer()

    approval = guard.approve_transfer("admin", result["approval_id"])

    assert approval["allowed"] is True
    assert get_balance("ACC-1001")["balance"] == before["ACC-1001"] - 100
    assert get_balance("ACC-1002")["balance"] == before["ACC-1002"] + 100
    assert result["approval_id"] not in guard.PENDING_APPROVALS


def test_rejected_transfer_does_not_move_money():
    before, result = queue_transfer()

    rejection = guard.reject_transfer("admin", result["approval_id"])

    assert rejection["allowed"] is True
    assert rejection["status"] == "rejected"
    assert balances() == before
    assert result["approval_id"] not in guard.PENDING_APPROVALS


def test_unauthorized_approver_cannot_approve_transfer():
    before, result = queue_transfer()

    approval = guard.approve_transfer("riya", result["approval_id"])

    assert approval["allowed"] is False
    assert balances() == before
    assert result["approval_id"] in guard.PENDING_APPROVALS


def test_approval_id_cannot_be_reused():
    _, result = queue_transfer()
    approval_id = result["approval_id"]

    first = guard.approve_transfer("admin", approval_id)
    balances_after_first = balances()
    second = guard.approve_transfer("admin", approval_id)

    assert first["allowed"] is True
    assert second["allowed"] is False
    assert balances() == balances_after_first

