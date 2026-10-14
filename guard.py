
import json
import math
import os
import uuid
from datetime import datetime, timezone

from bank import get_balance, transfer
from risk import assess_risk

TOOL_INVENTORY = {
    "get_balance": {
        "risk_level": "low",
        "required_args": {"account_id"},
        "account_arg": "account_id",
        "permitted_callers": {
            "riya": {"ACC-1001", "ACC-1002"},
            "arjun": {"ACC-2001"},
        },
    },
    "transfer": {
        "risk_level": "high",
        "required_args": {"from_account", "to_account", "amount"},
        "account_arg": "from_account",
        "destination_arg": "to_account",
        "permitted_callers": {
            "riya": {"ACC-1001", "ACC-1002"},
            "arjun": {"ACC-2001"},
        },
    },
}

AUDIT_LOG = []
SECURITY_ALERTS = []
PENDING_APPROVALS = {}

# Demo-only approver identity. Replace with real authentication
# and authorization before using outside the hackathon prototype.
APPROVER_IDS = {"admin"}

AUDIT_LOG_PATH = os.environ.get(
    "MCP_GUARD_AUDIT_LOG", "audit.jsonl"
)
SECURITY_ALERTS_PATH = os.environ.get(
    "MCP_GUARD_SECURITY_ALERTS_LOG", "security_alerts.jsonl"
)


def load_audit_log(*, _log_path=None):
    """Load valid audit objects from JSONL, skipping malformed entries."""
    path = _log_path if _log_path is not None else AUDIT_LOG_PATH
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        entries.append(item)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
    except OSError:
        pass
    return entries


AUDIT_LOG.extend(load_audit_log())


def load_security_alerts(*, _log_path=None):
    """Load valid alert objects from JSONL, skipping malformed entries."""
    path = _log_path if _log_path is not None else SECURITY_ALERTS_PATH
    alerts = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        alerts.append(item)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
    except FileNotFoundError:
        pass
    except OSError:
        pass
    return alerts


SECURITY_ALERTS.extend(load_security_alerts())


def record_security_alert(entry, *, _log_path=None):
    """Keep an alert in memory and append it to persistent JSONL storage."""
    alert = dict(entry)
    SECURITY_ALERTS.append(alert)

    path = _log_path if _log_path is not None else SECURITY_ALERTS_PATH
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(alert) + "\n")
    except Exception:
        # Alert logging failures must not expose internal details.
        pass


def audit(user_id, tool, allowed, reason, *, _log_path=None):
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "tool": tool,
        "allowed": allowed,
        "reason": reason,
    }
    AUDIT_LOG.append(entry)

    if not allowed or "high-risk" in reason.lower():
        record_security_alert(entry)

    path = _log_path if _log_path is not None else AUDIT_LOG_PATH
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        # Logging failures must not expose internal details.
        pass


def handle_request(request):
    if not isinstance(request, dict):
        audit("unknown", "unknown", False, "Invalid request")
        return {"allowed": False, "reason": "Invalid request"}

    user_id = request.get("user_id")
    tool = request.get("tool")
    args = request.get("arguments")

    if not isinstance(user_id, str) or not user_id:
        audit("unknown", str(tool), False, "Invalid user_id")
        return {"allowed": False, "reason": "Invalid user_id"}

    if not isinstance(tool, str):
        audit(user_id, str(tool), False, "Tool not allowed")
        return {"allowed": False, "reason": "Tool not allowed"}

    tool_spec = TOOL_INVENTORY.get(tool)
    if tool_spec is None:
        audit(user_id, str(tool), False, "Tool not allowed")
        return {"allowed": False, "reason": "Tool not allowed"}

    if not isinstance(args, dict):
        audit(user_id, tool, False, "Arguments must be an object")
        return {
            "allowed": False,
            "reason": "Arguments must be an object",
        }

    if set(args) != tool_spec["required_args"]:
        audit(user_id, tool, False, "Invalid arguments")
        return {"allowed": False, "reason": "Invalid arguments"}

    risk = assess_risk(tool, args)

    if "amount" in tool_spec["required_args"]:
        amount = args["amount"]

        if isinstance(amount, bool) or not isinstance(
            amount, (int, float)
        ):
            audit(user_id, tool, False, "Amount must be numeric")
            return {
                "allowed": False,
                "reason": "Amount must be numeric",
            }

        if isinstance(amount, float) and not math.isfinite(amount):
            audit(user_id, tool, False, "Amount must be finite")
            return {
                "allowed": False,
                "reason": "Amount must be finite",
            }

        if amount > 10_000:
            audit(user_id, tool, False, "Amount exceeds maximum transfer limit of 10000")
            return {"allowed": False, "reason": "Amount exceeds maximum transfer limit of 10000"}

        if amount <= 0:
            audit(user_id, tool, False, "Amount must be positive")
            return {
                "allowed": False,
                "reason": "Amount must be positive",
            }

    account_id = args[tool_spec["account_arg"]]

    if not isinstance(account_id, str):
        audit(user_id, tool, False, "Invalid account ID")
        return {"allowed": False, "reason": "Invalid account ID"}

    permitted = tool_spec["permitted_callers"].get(user_id, set())

    if account_id not in permitted:
        audit(user_id, tool, False, "User not authorized for account")
        return {
            "allowed": False,
            "reason": "User not authorized for account",
        }

    if "destination_arg" in tool_spec:
        destination = args[tool_spec["destination_arg"]]

        if not isinstance(destination, str):
            audit(user_id, tool, False, "Invalid destination account")
            return {
                "allowed": False,
                "reason": "Invalid destination account",
            }

        if destination == account_id:
            audit(
                user_id,
                tool,
                False,
                "Source and destination accounts must differ",
            )
            return {
                "allowed": False,
                "reason": "Source and destination accounts must differ",
            }

        if destination not in permitted:
            audit(
                user_id,
                tool,
                False,
                "User not authorized for destination",
            )
            return {
                "allowed": False,
                "reason": "User not authorized for destination",
            }

        # High-risk transfers are queued and do not move money here.
        approval_id = str(uuid.uuid4())
        PENDING_APPROVALS[approval_id] = {
            "user_id": user_id,
            "arguments": dict(args),
            "risk": risk,
        }

        audit(
            user_id,
            tool,
            True,
            f"Pending approval; risk={risk['level']}; score={risk['score']}",
        )
        if risk["level"] == "high":
            record_security_alert({
                "time": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "tool": tool,
                "allowed": True,
                "reason": f"High-risk request; score={risk['score']}",
            })
        return {
            "allowed": True,
            "status": "pending_approval",
            "approval_id": approval_id,
            "risk": risk,
            "message": "Transfer queued; no money moved yet.",
        }

    try:
        result = get_balance(account_id)
    except (KeyError, ValueError) as exc:
        audit(user_id, tool, False, str(exc))
        return {"allowed": False, "reason": str(exc)}
    except Exception:
        audit(user_id, tool, False, "Internal error")
        return {"allowed": False, "reason": "Internal error"}

    audit(
        user_id,
        tool,
        True,
        f"Policy checks passed; risk={risk['level']}; score={risk['score']}",
    )
    return {"allowed": True, "result": result, "risk": risk}


def approve_transfer(approver_id, approval_id):
    if approver_id not in APPROVER_IDS:
        audit(str(approver_id), "transfer", False, "Approver not authorized")
        return {"allowed": False, "reason": "Approver not authorized"}

    if not isinstance(approval_id, str):
        audit(approver_id, "transfer", False, "Invalid approval ID")
        return {"allowed": False, "reason": "Invalid approval ID"}

    pending = PENDING_APPROVALS.pop(approval_id, None)
    if pending is None:
        audit(approver_id, "transfer", False, "Approval not found")
        return {"allowed": False, "reason": "Approval not found"}

    args = pending["arguments"]
    requester = pending["user_id"]

    try:
        result = transfer(
            args["from_account"],
            args["to_account"],
            args["amount"],
        )
    except (KeyError, ValueError) as exc:
        audit(requester, "transfer", False, str(exc))
        audit(approver_id, "approve_transfer", False, "Transfer failed")
        return {"allowed": False, "reason": str(exc)}
    except Exception:
        audit(requester, "transfer", False, "Internal error")
        audit(approver_id, "approve_transfer", False, "Transfer failed")
        return {"allowed": False, "reason": "Internal error"}

    audit(requester, "transfer", True, "Transfer approved and executed")
    audit(approver_id, "approve_transfer", True, "Approval completed")
    return {"allowed": True, "result": result}


def reject_transfer(approver_id, approval_id):
    if approver_id not in APPROVER_IDS:
        audit(str(approver_id), "transfer", False, "Approver not authorized")
        return {"allowed": False, "reason": "Approver not authorized"}

    if not isinstance(approval_id, str):
        audit(approver_id, "transfer", False, "Invalid approval ID")
        return {"allowed": False, "reason": "Invalid approval ID"}

    pending = PENDING_APPROVALS.pop(approval_id, None)
    if pending is None:
        audit(approver_id, "transfer", False, "Approval not found")
        return {"allowed": False, "reason": "Approval not found"}

    audit(pending["user_id"], "transfer", False, "Transfer rejected")
    audit(approver_id, "reject_transfer", True, "Rejection completed")
    return {"allowed": True, "status": "rejected"}


if __name__ == "__main__":
    demo_request = {
        "user_id": "riya",
        "tool": "get_balance",
        "arguments": {"account_id": "ACC-1001"},
    }
    print(json.dumps(handle_request(demo_request), indent=2))

    print("\nAudit log:")
    print(json.dumps(AUDIT_LOG, indent=2))
