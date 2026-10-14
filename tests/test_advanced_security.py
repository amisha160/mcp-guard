from math import inf, nan

import pytest
import guard
from risk import assess_risk


@pytest.mark.parametrize("bad_input", [
    None,
    [],
    "invalid",
    123,
])
def test_non_dictionary_requests_are_rejected(bad_input):
    result = guard.handle_request(bad_input)
    assert result["allowed"] is False


def test_empty_user_id_is_rejected():
    result = guard.handle_request({
        "user_id": "",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    })
    assert result["allowed"] is False


def test_unknown_tool_is_rejected():
    result = guard.handle_request({
        "user_id": "riya",
        "tool": "delete_everything",
        "arguments": {},
    })
    assert result["allowed"] is False


def test_non_dictionary_arguments_are_rejected():
    result = guard.handle_request({
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": ["ACC-1001"],
    })
    assert result["allowed"] is False


@pytest.mark.parametrize("amount", [
    True,
    False,
    nan,
    inf,
    -inf,
    0,
    -1,
    10001,
])
def test_invalid_transfer_amounts_are_rejected(amount):
    result = guard.handle_request({
        "user_id": "riya",
        "tool": "transfer",
        "arguments": {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": amount,
        },
    })
    assert result["allowed"] is False


def test_same_account_transfer_is_rejected():
    result = guard.handle_request({
        "user_id": "riya",
        "tool": "transfer",
        "arguments": {
            "from_account": "ACC-1001",
            "to_account": "ACC-1001",
            "amount": 10,
        },
    })
    assert result["allowed"] is False


def test_same_account_transfer_is_scored_high_risk():
    result = assess_risk("transfer", {
        "from_account": "ACC-1001",
        "to_account": "ACC-1001",
        "amount": 10,
    })
    assert result["level"] == "high"
    assert "same_source_and_destination" in result["reasons"]


def test_unauthorized_approver_cannot_execute_transfer(monkeypatch):
    calls = []
    monkeypatch.setattr(
        guard, "transfer",
        lambda *args: calls.append(args) or {"success": True},
    )

    request = guard.handle_request({
        "user_id": "riya",
        "tool": "transfer",
        "arguments": {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": 10,
        },
    })
    assert request["allowed"] is True

    result = guard.approve_transfer("not-an-admin", request["approval_id"])
    assert result["allowed"] is False
    assert calls == []


def test_approval_id_cannot_execute_transfer_twice(monkeypatch):
    calls = []
    monkeypatch.setattr(
        guard, "transfer",
        lambda *args: calls.append(args) or {"success": True},
    )

    request = guard.handle_request({
        "user_id": "riya",
        "tool": "transfer",
        "arguments": {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": 10,
        },
    })
    approval_id = request["approval_id"]

    first = guard.approve_transfer("admin", approval_id)
    second = guard.approve_transfer("admin", approval_id)

    assert first["allowed"] is True
    assert second["allowed"] is False
    assert len(calls) == 1
