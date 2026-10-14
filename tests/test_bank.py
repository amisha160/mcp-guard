
import math
import pytest

from bank import ACCOUNTS, transfer


@pytest.fixture(autouse=True)
def reset_accounts():
    original_balances = {
        account: details["balance"]
        for account, details in ACCOUNTS.items()
    }
    yield
    for account, balance in original_balances.items():
        ACCOUNTS[account]["balance"] = balance


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
        True,
        False,
        "100",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_invalid_amount_is_rejected_without_changing_balances(amount):
    before = {
        account: details["balance"]
        for account, details in ACCOUNTS.items()
    }

    with pytest.raises(ValueError):
        transfer("ACC-1001", "ACC-1002", amount)

    after = {
        account: details["balance"]
        for account, details in ACCOUNTS.items()
    }
    assert after == before


def test_valid_transfer_changes_balances_correctly():
    source_before = ACCOUNTS["ACC-1001"]["balance"]
    destination_before = ACCOUNTS["ACC-1002"]["balance"]

    result = transfer("ACC-1001", "ACC-1002", 100)

    assert result["status"] == "simulated"
    assert math.isclose(
        ACCOUNTS["ACC-1001"]["balance"], source_before - 100
    )
    assert math.isclose(
        ACCOUNTS["ACC-1002"]["balance"], destination_before + 100
    )
