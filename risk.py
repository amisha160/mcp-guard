"""Deterministic risk scoring for MCP Guard requests."""

from math import isfinite


def assess_risk(tool, arguments):
    """Return a risk score, level, and reasons for a request.

    Scores are advisory. Authorization and input validation in guard.py
    must remain the enforcement boundary.
    """
    score = 0
    reasons = []

    if tool not in {"get_balance", "transfer"}:
        score += 100
        reasons.append("unknown_tool")

    if not isinstance(arguments, dict):
        return {
            "score": 100,
            "level": "high",
            "reasons": ["invalid_arguments"],
        }

    if tool == "transfer":
        score += 40
        reasons.append("money_movement")

        amount = arguments.get("amount")

        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            score += 60
            reasons.append("invalid_amount")
        elif not isfinite(amount) or amount <= 0 or amount > 10_000:
            score += 60
            reasons.append("amount_out_of_policy")

        if arguments.get("from_account") == arguments.get("to_account"):
            score += 30
            reasons.append("same_source_and_destination")

    elif tool == "get_balance":
        score += 5

    score = min(score, 100)

    if score >= 70:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
    }