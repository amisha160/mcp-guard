import json
import math
from datetime import datetime, timezone

from bank import get_balance, transfer

ALLOWED_TOOLS = {"get_balance", "transfer"}

USER_ACCOUNTS = {
    "riya": {"ACC-1001", "ACC-1002"},
    "arjun": {"ACC-2001"},
}

AUDIT_LOG = []


def audit(user_id, tool, allowed, reason):
    AUDIT_LOG.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "tool": tool,
        "allowed": allowed,
        "reason": reason,
    })


def handle_request(request):
    user_id = request.get("user_id")
    tool = request.get("tool")
    args = request.get("arguments")

    if not isinstance(user_id, str) or not user_id:
        audit("unknown", str(tool), False, "Invalid user_id")
        return {"allowed": False, "reason": "Invalid user_id"}

    if tool not in ALLOWED_TOOLS:
        audit(user_id, str(tool), False, "Tool not allowed")
        return {"allowed": False, "reason": "Tool not allowed"}

    if not isinstance(args, dict):
        audit(user_id, tool, False, "Arguments must be an object")
        return {"allowed": False, "reason": "Arguments must be an object"}

    if tool == "get_balance":
        if set(args) != {"account_id"}:
            audit(user_id, tool, False, "Invalid arguments")
            return {"allowed": False, "reason": "Invalid arguments"}
        account_id = args["account_id"]

    elif tool == "transfer":
        if set(args) != {"from_account", "to_account", "amount"}:
            audit(user_id, tool, False, "Invalid arguments")
            return {"allowed": False, "reason": "Invalid arguments"}

        account_id = args["from_account"]
        amount = args["amount"]

        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            audit(user_id, tool, False, "Amount must be numeric")
            return {"allowed": False, "reason": "Amount must be numeric"}

        if isinstance(amount, float) and not math.isfinite(amount):
            audit(user_id, tool, False, "Amount must be finite")
            return {"allowed": False, "reason": "Amount must be finite"}

        if amount <= 0:
            audit(user_id, tool, False, "Amount must be positive")
            return {"allowed": False, "reason": "Amount must be positive"}

    if not isinstance(account_id, str):
        audit(user_id, tool, False, "Invalid account ID")
        return {"allowed": False, "reason": "Invalid account ID"}

    if account_id not in USER_ACCOUNTS.get(user_id, set()):
        audit(user_id, tool, False, "User not authorized for account")
        return {"allowed": False, "reason": "User not authorized for account"}

    if tool == "transfer":
        destination = args["to_account"]
        if not isinstance(destination, str):
            audit(user_id, tool, False, "Invalid destination account")
            return {"allowed": False, "reason": "Invalid destination account"}

        if destination not in USER_ACCOUNTS.get(user_id, set()):
            audit(user_id, tool, False, "User not authorized for destination")
            return {
                "allowed": False,
                "reason": "User not authorized for destination",
            }

    try:
        if tool == "get_balance":
            result = get_balance(account_id)
        else:
            result = transfer(
                args["from_account"],
                args["to_account"],
                args["amount"],
            )
    except (KeyError, ValueError) as exc:
        audit(user_id, tool, False, str(exc))
        return {"allowed": False, "reason": str(exc)}

    audit(user_id, tool, True, "Policy checks passed")
    return {"allowed": True, "result": result}


if __name__ == "__main__":
    demo_request = {
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    }
    print(json.dumps(handle_request(demo_request), indent=2))
    print(json.dumps(AUDIT_LOG, indent=2))
