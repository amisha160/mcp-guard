
# Fictional data only. Never use real banking or personal information.

ACCOUNTS = {
    "ACC-1001": {"balance": 25000.00},
    "ACC-1002": {"balance": 8000.00},
    "ACC-2001": {"balance": 40000.00},
}


def get_balance(account_id):
    """Return the balance for an existing fictional account."""
    if account_id not in ACCOUNTS:
        raise KeyError("Unknown account")

    return {
        "account_id": account_id,
        "balance": ACCOUNTS[account_id]["balance"],
        "currency": "INR",
    }


def transfer(from_account, to_account, amount):
    """Transfer fictional funds between two existing demo accounts."""
    if from_account not in ACCOUNTS or to_account not in ACCOUNTS:
        raise KeyError("Unknown account")

    if from_account == to_account:
        raise ValueError("Source and destination must differ")

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("Amount must be numeric")

    if amount <= 0:
        raise ValueError("Amount must be positive")

    if ACCOUNTS[from_account]["balance"] < amount:
        raise ValueError("Insufficient funds")

    ACCOUNTS[from_account]["balance"] -= amount
    ACCOUNTS[to_account]["balance"] += amount

    return {
        "status": "simulated",
        "from_account": from_account,
        "to_account": to_account,
        "amount": amount,
        "currency": "INR",
    }


if __name__ == "__main__":
    print("Initial balance:")
    print(get_balance("ACC-1001"))

    print("\nSimulated transfer:")
    print(transfer("ACC-1001", "ACC-1002", 500))

    print("\nBalance after transfer:")
    print(get_balance("ACC-1001"))
