import json
import math
import os
from datetime import datetime, timezone

from bank import get_balance, transfer

# ---------------------------------------------------------------------------
# Explicit tool inventory.
# Each entry defines what the tool is, its risk level, which argument keys it
# accepts (exact set), which argument names carry account IDs for authorization,
# and which callers may use it.
#
# This is the single source of truth for policy enforcement.  Adding a new tool
# means adding one entry here; no changes to handle_request are required.
# ---------------------------------------------------------------------------
TOOL_INVENTORY = {
    "get_balance": {
        "risk_level": "low",
        "required_args": {"account_id"},
        # The argument that holds the caller's source account ID.
        "account_arg": "account_id",
        # user_id -> set of account IDs the user may access with this tool.
        "permitted_callers": {
            "riya":  {"ACC-1001", "ACC-1002"},
            "arjun": {"ACC-2001"},
        },
    },
    "transfer": {
        "risk_level": "high",
        "required_args": {"from_account", "to_account", "amount"},
        "account_arg": "from_account",
        # When present, the destination account is also checked against the
        # caller's permitted set.
        "destination_arg": "to_account",
        "permitted_callers": {
            "riya":  {"ACC-1001", "ACC-1002"},
            "arjun": {"ACC-2001"},
        },
    },
}

AUDIT_LOG = []

# Default path for the persistent JSONL audit log.
# Each line is one JSON object.  Set AUDIT_LOG_PATH before importing (or
# monkey-patch it in tests) to redirect the file.  Pass _log_path to audit()
# directly when you need per-call control (e.g. pytest tmp_path).
AUDIT_LOG_PATH = os.environ.get("MCP_GUARD_AUDIT_LOG", "audit.jsonl")


def audit(user_id, tool, allowed, reason, *, _log_path=None):
    """Append one entry to the in-memory log and to the JSONL file.

    File-write failures are silenced so that a disk error never prevents a
    correctly-denied request from returning its blocked response.
    """
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "tool": tool,
        "allowed": allowed,
        "reason": reason,
    }
    AUDIT_LOG.append(entry)

    path = _log_path if _log_path is not None else AUDIT_LOG_PATH
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:  # noqa: BLE001
        # Never let a logging failure surface to the caller.
        pass


def handle_request(request):
    user_id = request.get("user_id")
    tool = request.get("tool")
    args = request.get("arguments")

    if not isinstance(user_id, str) or not user_id:
        audit("unknown", str(tool), False, "Invalid user_id")
        return {"allowed": False, "reason": "Invalid user_id"}

    tool_spec = TOOL_INVENTORY.get(tool)
    if tool_spec is None:
        audit(user_id, str(tool), False, "Tool not allowed")
        return {"allowed": False, "reason": "Tool not allowed"}

    if not isinstance(args, dict):
        audit(user_id, tool, False, "Arguments must be an object")
        return {"allowed": False, "reason": "Arguments must be an object"}

    if set(args) != tool_spec["required_args"]:
        audit(user_id, tool, False, "Invalid arguments")
        return {"allowed": False, "reason": "Invalid arguments"}

    # Amount validation applies to any tool that accepts an "amount" argument.
    if "amount" in tool_spec["required_args"]:
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

    # Source account authorization.
    account_id = args[tool_spec["account_arg"]]

    if not isinstance(account_id, str):
        audit(user_id, tool, False, "Invalid account ID")
        return {"allowed": False, "reason": "Invalid account ID"}

    permitted = tool_spec["permitted_callers"].get(user_id, set())

    if account_id not in permitted:
        audit(user_id, tool, False, "User not authorized for account")
        return {"allowed": False, "reason": "User not authorized for account"}

    # Destination account authorization (tools that declare a destination_arg).
    if "destination_arg" in tool_spec:
        destination = args[tool_spec["destination_arg"]]
        if not isinstance(destination, str):
            audit(user_id, tool, False, "Invalid destination account")
            return {"allowed": False, "reason": "Invalid destination account"}

        if destination not in permitted:
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
    except Exception:
        # Unexpected exception from a bank function.  Audit with a fixed
        # reason so no internal detail leaks to the caller.
        audit(user_id, tool, False, "Internal error")
        return {"allowed": False, "reason": "Internal error"}

    audit(user_id, tool, True, "Policy checks passed")
    return {"allowed": True, "result": result}


if __name__ == "__main__":
    demo_request = {
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    }
    print(json.dumps(handle_request(demo_request), indent=2))

    blocked_request = {
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-2001"},
    }
    print("\nBlocked request:")
    print(json.dumps(handle_request(blocked_request), indent=2))

    print("\nAudit log:")
    print(json.dumps(AUDIT_LOG, indent=2))
