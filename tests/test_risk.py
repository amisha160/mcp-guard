import pytest

from risk import assess_risk


def test_authorized_balance_request_has_low_advisory_risk():
    result = assess_risk("get_balance", {"account_id": "ACC-1001"})

    assert result["level"] == "low"
    assert result["score"] < 30


def test_transfer_is_classified_as_medium_risk():
    result = assess_risk(
        "transfer",
        {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": 100,
        },
    )

    assert result["level"] == "medium"
    assert result["score"] == 40
    assert "money_movement" in result["reasons"]


@pytest.mark.parametrize("amount", [True, "100", None, float("nan"), float("inf"), 0, -1, 10001])
def test_invalid_transfer_amount_is_high_risk(amount):
    result = assess_risk(
        "transfer",
        {
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": amount,
        },
    )

    assert result["level"] == "high"
    assert result["score"] >= 70


def test_unknown_tool_is_high_risk():
    result = assess_risk("delete_everything", {})

    assert result["level"] == "high"
    assert "unknown_tool" in result["reasons"]


def test_non_object_arguments_are_high_risk():
    result = assess_risk("transfer", None)

    assert result["level"] == "high"
    assert result["score"] == 100


def test_same_source_and_destination_increases_risk():
    result = assess_risk(
        "transfer",
        {
            "from_account": "ACC-1001",
            "to_account": "ACC-1001",
            "amount": 100,
        },
    )

    assert result["level"] == "high"
    assert "same_source_and_destination" in result["reasons"]