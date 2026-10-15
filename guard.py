"""
guard.py — MCP Guard security policy engine.

This module is the single authoritative entry point for all tool invocations.
No caller may bypass it.

Public API (backwards-compatible)
----------------------------------
  handle_request(request)            → dict
  approve_transfer(approver_id, approval_id) → dict
  reject_transfer(approver_id, approval_id)  → dict

Module-level state (used by tests and the dashboard)
------------------------------------------------------
  AUDIT_LOG          — in-memory list of audit dicts (session lifetime)
  PENDING_APPROVALS  — dict of approval_id → pending transfer record
  TOOL_INVENTORY     — dict of tool metadata
  APPROVER_IDS       — set of valid approver identity strings
  AUDIT_LOG_PATH     — path to the persistent JSONL audit file

Security properties
-------------------
  • Deny-by-default for unknown tools, users, and accounts.
  • Exact argument-schema validation before any business logic runs.
  • All numeric edge cases handled before the bank layer sees values.
  • Approval IDs are UUID4 — single-use, unguessable.
  • Approvals expire after APPROVAL_TTL_SECONDS seconds.
  • Risk score attached to every audit entry.
  • Hash-chained integrity audit log (audit_integrity.jsonl).
  • Abuse checks: rate-limit, denial streak, replay, oversized input.
  • Revalidation of auth and transfer details at approval time.

Known prototype limitations
----------------------------
  • user_id is self-declared — no real authentication.
  • State is in-memory; resets on process restart (except audit files).
  • "admin" approver is a demo stub, not a real identity.

⚠ SIMULATION — fictional accounts only.
"""

from __future__ import annotations

import json
import math
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from bank import get_balance, transfer
import config
import audit_integrity
from abuse import (
    AbuseViolation,
    check_input_sizes,
    check_rate_limit,
    check_replay,
    get_denial_streak,
    get_request_count,
    record_outcome,
)
from risk import evaluate as _risk_evaluate

# ── Module-level state ─────────────────────────────────────────────────────────

TOOL_INVENTORY: dict[str, Any] = {
    "get_balance": {
        "risk_level": "low",
        "required_args": {"account_id"},
        "account_arg": "account_id",
        "permitted_callers": {
            "riya":  {"ACC-1001", "ACC-1002"},
            "arjun": {"ACC-2001"},
        },
    },
    "transfer": {
        "risk_level": "high",
        "required_args": {"from_account", "to_account", "amount"},
        "account_arg": "from_account",
        "destination_arg": "to_account",
        "permitted_callers": {
            "riya":  {"ACC-1001", "ACC-1002"},
            "arjun": {"ACC-2001"},
        },
    },
}

AUDIT_LOG: list[dict[str, Any]] = []
PENDING_APPROVALS: dict[str, Any] = {}

# Demo-only approver identity.  In production: replace with a real auth system.
APPROVER_IDS: set[str] = set(config.APPROVER_IDS)

AUDIT_LOG_PATH: str = config.AUDIT_LOG_PATH

# Internal lock for approval state mutations
_approval_lock = threading.Lock()


# ── Audit helpers ──────────────────────────────────────────────────────────────

def audit(
    user_id: str,
    tool: str,
    allowed: bool,
    reason: str,
    *,
    request_id: str | None = None,
    risk: dict[str, Any] | None = None,
    approval_id: str | None = None,
    _log_path: str | None = None,
) -> None:
    """
    Write one audit entry to both the in-memory log and the persistent logs.

    Fields
    ------
    time        — ISO 8601 UTC timestamp
    request_id  — caller-supplied or guard-generated correlation ID
    user_id     — declared caller identity
    tool        — tool name
    allowed     — authorization decision
    reason      — human-readable decision rationale
    risk_score  — float risk score [0.0, 1.0] (if evaluated)
    risk_cat    — risk category string (if evaluated)
    risk_factors— list of human-readable risk factors (if evaluated)
    approval_id — UUID of the pending approval record (transfers only)
    """
    entry: dict[str, Any] = {
        "time":       datetime.now(timezone.utc).isoformat(),
        "request_id": request_id or "",
        "user_id":    user_id,
        "tool":       tool,
        "allowed":    allowed,
        "reason":     reason,
    }
    if risk:
        entry["risk_score"]   = risk.get("score")
        entry["risk_cat"]     = risk.get("category")
        entry["risk_factors"] = risk.get("factors", [])
    if approval_id:
        entry["approval_id"] = approval_id

    AUDIT_LOG.append(entry)

    # ── Persistent JSONL log ───────────────────────────────────────────────────
    path = _log_path if _log_path is not None else AUDIT_LOG_PATH
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Logging failures must not expose internal details

    # ── Integrity-chained log ──────────────────────────────────────────────────
    try:
        audit_integrity.append(entry)
    except Exception:
        pass


# ── Main policy-engine entry point ─────────────────────────────────────────────

def handle_request(request: Any) -> dict[str, Any]:
    """
    Evaluate and enforce policy for a single tool invocation.

    Parameters
    ----------
    request : dict with keys user_id, tool, arguments, and optional request_id.

    Returns
    -------
    dict — always contains 'allowed' (bool) and either 'result'/'approval_id'
           on success or 'reason' on denial.
    """
    # ── Structural check ───────────────────────────────────────────────────────
    if not isinstance(request, dict):
        audit("unknown", "unknown", False, "Invalid request")
        return {"allowed": False, "reason": "Invalid request"}

    user_id    = request.get("user_id")
    tool       = request.get("tool")
    args       = request.get("arguments")
    request_id = request.get("request_id") or str(uuid.uuid4())

    # ── user_id validation ─────────────────────────────────────────────────────
    if not isinstance(user_id, str) or not user_id:
        audit("unknown", str(tool), False, "Invalid user_id",
              request_id=request_id)
        return {"allowed": False, "reason": "Invalid user_id"}

    # ── Input-size abuse check ─────────────────────────────────────────────────
    try:
        check_input_sizes(user_id=user_id, tool=tool)
    except AbuseViolation as exc:
        reason = str(exc)
        audit(user_id, str(tool), False, reason, request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": reason}

    # ── Replay check ──────────────────────────────────────────────────────────
    try:
        check_replay(request.get("request_id"))
    except AbuseViolation as exc:
        reason = str(exc)
        audit(user_id, str(tool), False, reason, request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": reason}

    # ── Rate-limit check ──────────────────────────────────────────────────────
    try:
        check_rate_limit(user_id)
    except AbuseViolation as exc:
        reason = str(exc)
        audit(user_id, str(tool), False, reason, request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": reason}

    # ── Tool allowlist ────────────────────────────────────────────────────────
    tool_spec = TOOL_INVENTORY.get(tool)
    if tool_spec is None:
        audit(user_id, str(tool), False, "Tool not allowed",
              request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": "Tool not allowed"}

    # ── Arguments must be a dict ───────────────────────────────────────────────
    if not isinstance(args, dict):
        audit(user_id, tool, False, "Arguments must be an object",
              request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": "Arguments must be an object"}

    # ── Exact argument schema ──────────────────────────────────────────────────
    if set(args) != tool_spec["required_args"]:
        audit(user_id, tool, False, "Invalid arguments", request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": "Invalid arguments"}

    # ── Amount validation (transfers only) ────────────────────────────────────
    if "amount" in tool_spec["required_args"]:
        amount = args["amount"]

        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            audit(user_id, tool, False, "Amount must be numeric",
                  request_id=request_id)
            record_outcome(user_id, allowed=False)
            return {"allowed": False, "reason": "Amount must be numeric"}

        if not math.isfinite(amount):
            audit(user_id, tool, False, "Amount must be finite",
                  request_id=request_id)
            record_outcome(user_id, allowed=False)
            return {"allowed": False, "reason": "Amount must be finite"}

        if amount <= 0:
            audit(user_id, tool, False, "Amount must be positive",
                  request_id=request_id)
            record_outcome(user_id, allowed=False)
            return {"allowed": False, "reason": "Amount must be positive"}

        if amount > config.MAX_TRANSFER_AMOUNT:
            msg = (
                f"Amount exceeds maximum transfer limit of "
                f"{config.MAX_TRANSFER_AMOUNT}"
            )
            audit(user_id, tool, False, msg, request_id=request_id)
            record_outcome(user_id, allowed=False)
            return {"allowed": False, "reason": msg}

    # ── Account ownership ──────────────────────────────────────────────────────
    account_id = args[tool_spec["account_arg"]]
    if not isinstance(account_id, str):
        audit(user_id, tool, False, "Invalid account ID",
              request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": "Invalid account ID"}

    permitted = tool_spec["permitted_callers"].get(user_id, set())
    if account_id not in permitted:
        audit(user_id, tool, False, "User not authorized for account",
              request_id=request_id)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": "User not authorized for account"}

    # ── Destination account check (transfers) ─────────────────────────────────
    if "destination_arg" in tool_spec:
        destination = args[tool_spec["destination_arg"]]
        if not isinstance(destination, str):
            audit(user_id, tool, False, "Invalid destination account",
                  request_id=request_id)
            record_outcome(user_id, allowed=False)
            return {"allowed": False, "reason": "Invalid destination account"}

        if destination not in permitted:
            audit(user_id, tool, False, "User not authorized for destination",
                  request_id=request_id)
            record_outcome(user_id, allowed=False)
            return {
                "allowed": False,
                "reason": "User not authorized for destination",
            }

    # ── Risk evaluation ────────────────────────────────────────────────────────
    risk_result = _risk_evaluate(
        tool=tool,
        user_id=user_id,
        arguments=args,
        recent_denial_count=get_denial_streak(user_id),
        recent_request_count=get_request_count(user_id),
    )
    risk_dict = risk_result.to_dict()

    # Hard deny on critical risk (even if all other checks pass)
    if risk_result.action == "deny":
        reason = (
            f"Request denied by risk engine (score={risk_result.score:.2f}, "
            f"category={risk_result.category})"
        )
        audit(user_id, tool, False, reason,
              request_id=request_id, risk=risk_dict)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": reason, "risk": risk_dict}

    # ── Transfer → queue for approval ─────────────────────────────────────────
    if "destination_arg" in tool_spec:
        approval_id = str(uuid.uuid4())
        now_utc     = datetime.now(timezone.utc)

        with _approval_lock:
            PENDING_APPROVALS[approval_id] = {
                "user_id":    user_id,
                "arguments":  dict(args),
                "request_id": request_id,
                "queued_at":  now_utc.isoformat(),
                "expires_at": _expires_at(now_utc),
                "status":     "pending",
                "risk":       risk_dict,
            }

        audit(user_id, tool, True, "Pending approval",
              request_id=request_id, risk=risk_dict, approval_id=approval_id)
        record_outcome(user_id, allowed=True)
        return {
            "allowed":     True,
            "status":      "pending_approval",
            "approval_id": approval_id,
            "message":     "Transfer queued; no money moved yet.",
            "risk":        risk_dict,
        }

    # ── Execute read-only operation ────────────────────────────────────────────
    try:
        result = get_balance(account_id)
    except (KeyError, ValueError) as exc:
        audit(user_id, tool, False, str(exc),
              request_id=request_id, risk=risk_dict)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": str(exc)}
    except Exception:
        audit(user_id, tool, False, "Internal error",
              request_id=request_id, risk=risk_dict)
        record_outcome(user_id, allowed=False)
        return {"allowed": False, "reason": "Internal error"}

    audit(user_id, tool, True, "Policy checks passed",
          request_id=request_id, risk=risk_dict)
    record_outcome(user_id, allowed=True)
    return {"allowed": True, "result": result, "risk": risk_dict}


# ── Approval helpers ───────────────────────────────────────────────────────────

def _expires_at(queued: datetime) -> str:
    """Return ISO 8601 expiry timestamp for a transfer queued at `queued`."""
    from datetime import timedelta
    return (queued + timedelta(seconds=config.APPROVAL_TTL_SECONDS)).isoformat()


def _is_expired(pending: dict[str, Any]) -> bool:
    """Return True if a pending approval has passed its expiry time."""
    expires_str = pending.get("expires_at")
    if not expires_str:
        return False
    try:
        expires = datetime.fromisoformat(expires_str)
        return datetime.now(timezone.utc) >= expires
    except (ValueError, TypeError):
        return False


# ── approve_transfer ───────────────────────────────────────────────────────────

def approve_transfer(approver_id: Any, approval_id: Any) -> dict[str, Any]:
    """
    Approve and execute a queued transfer.

    Re-validates:
      - Approver identity.
      - Approval ID existence and type.
      - Approval expiry.
      - Amount still within the configured limit.

    The approval is removed from PENDING_APPROVALS atomically before the
    transfer executes, preventing double-execution on concurrent calls.
    """
    if approver_id not in APPROVER_IDS:
        audit(str(approver_id), "transfer", False, "Approver not authorized")
        return {"allowed": False, "reason": "Approver not authorized"}

    if not isinstance(approval_id, str):
        audit(str(approver_id), "transfer", False, "Invalid approval ID")
        return {"allowed": False, "reason": "Invalid approval ID"}

    with _approval_lock:
        pending = PENDING_APPROVALS.get(approval_id)
        if pending is None:
            audit(str(approver_id), "transfer", False, "Approval not found")
            return {"allowed": False, "reason": "Approval not found"}

        # Expiry check
        if _is_expired(pending):
            PENDING_APPROVALS.pop(approval_id, None)
            audit(str(approver_id), "transfer", False, "Approval expired")
            return {"allowed": False, "reason": "Approval expired"}

        # Atomic pop — prevents double-execution
        PENDING_APPROVALS.pop(approval_id)

    args      = pending["arguments"]
    requester = pending["user_id"]

    # Re-validate amount at approval time
    amount = args.get("amount")
    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
        if amount > config.MAX_TRANSFER_AMOUNT:
            msg = "Transfer amount exceeds current limit at approval time"
            audit(requester, "transfer", False, msg)
            audit(str(approver_id), "approve_transfer", False,
                  "Revalidation failed")
            return {"allowed": False, "reason": msg}

    try:
        result = transfer(
            args["from_account"],
            args["to_account"],
            args["amount"],
        )
    except (KeyError, ValueError) as exc:
        audit(requester, "transfer", False, str(exc))
        audit(str(approver_id), "approve_transfer", False, "Transfer failed")
        return {"allowed": False, "reason": str(exc)}
    except Exception:
        audit(requester, "transfer", False, "Internal error")
        audit(str(approver_id), "approve_transfer", False, "Transfer failed")
        return {"allowed": False, "reason": "Internal error"}

    audit(requester, "transfer", True, "Transfer approved and executed",
          approval_id=approval_id)
    audit(str(approver_id), "approve_transfer", True, "Approval completed",
          approval_id=approval_id)
    return {"allowed": True, "result": result}


# ── reject_transfer ────────────────────────────────────────────────────────────

def reject_transfer(approver_id: Any, approval_id: Any) -> dict[str, Any]:
    """
    Reject and discard a queued transfer.

    No money ever moves.  The approval record is removed.
    """
    if approver_id not in APPROVER_IDS:
        audit(str(approver_id), "transfer", False, "Approver not authorized")
        return {"allowed": False, "reason": "Approver not authorized"}

    if not isinstance(approval_id, str):
        audit(str(approver_id), "transfer", False, "Invalid approval ID")
        return {"allowed": False, "reason": "Invalid approval ID"}

    with _approval_lock:
        pending = PENDING_APPROVALS.pop(approval_id, None)

    if pending is None:
        audit(str(approver_id), "transfer", False, "Approval not found")
        return {"allowed": False, "reason": "Approval not found"}

    audit(pending["user_id"], "transfer", False, "Transfer rejected",
          approval_id=approval_id)
    audit(str(approver_id), "reject_transfer", True, "Rejection completed",
          approval_id=approval_id)
    return {"allowed": True, "status": "rejected"}


# ── Expiry sweep utility ───────────────────────────────────────────────────────

def expire_stale_approvals() -> list[str]:
    """
    Remove and audit all approvals that have passed their expiry time.

    Returns the list of expired approval IDs.
    Call periodically (e.g. from the dashboard refresh loop).
    """
    now = datetime.now(timezone.utc)
    expired_ids: list[str] = []

    with _approval_lock:
        for ap_id, pending in list(PENDING_APPROVALS.items()):
            if _is_expired(pending):
                PENDING_APPROVALS.pop(ap_id)
                expired_ids.append(ap_id)

    for ap_id in expired_ids:
        audit("system", "transfer", False, "Approval expired (sweep)",
              approval_id=ap_id)

    return expired_ids


# ── CLI demo ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo_request = {
        "user_id":    "riya",
        "tool":       "get_balance",
        "arguments":  {"account_id": "ACC-1001"},
        "request_id": "demo-001",
    }
    print(json.dumps(handle_request(demo_request), indent=2))
    print("\nAudit log:")
    print(json.dumps(AUDIT_LOG, indent=2))
