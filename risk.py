"""
risk.py — Explainable risk evaluation engine for MCP Guard.

Every protected tool call is scored before execution.  The result is a
RiskResult dataclass containing:

  - score      float in [0.0, 1.0]  — higher = riskier
  - category   "low" | "medium" | "high" | "critical"
  - factors    list[str]  — human-readable reasons that raised the score
  - action     "allow" | "review" | "deny"

Design principles
-----------------
* Deterministic — same inputs always produce the same score.
* Explainable   — every point of risk is named in `factors`.
* No ML         — rule-based scoring; no probabilistic models.
* Configurable  — thresholds come from config.py.
* Testable      — pure function, no side-effects.

⚠ SIMULATION — does not use real fraud-detection data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import config


# ── Result type ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RiskResult:
    """Immutable risk evaluation output."""

    score: float                   # [0.0, 1.0]
    category: str                  # "low" | "medium" | "high" | "critical"
    factors: tuple[str, ...]       # human-readable risk factors
    action: str                    # "allow" | "review" | "deny"

    def to_dict(self) -> dict[str, Any]:
        return {
            "score":    round(self.score, 4),
            "category": self.category,
            "factors":  list(self.factors),
            "action":   self.action,
        }


# ── Internal helpers ───────────────────────────────────────────────────────────

def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _categorize(score: float) -> str:
    if score >= config.RISK_DENY:
        return "critical"
    if score >= config.RISK_REVIEW:
        return "high"
    if score >= 0.30:
        return "medium"
    return "low"


def _action(score: float) -> str:
    if score >= config.RISK_DENY:
        return "deny"
    if score >= config.RISK_REVIEW:
        return "review"
    return "allow"


# ── Main scoring function ──────────────────────────────────────────────────────

def evaluate(
    *,
    tool: str,
    user_id: str,
    arguments: dict[str, Any],
    recent_denial_count: int = 0,
    recent_request_count: int = 0,
) -> RiskResult:
    """
    Evaluate the risk of a proposed tool call.

    Parameters
    ----------
    tool                 : Name of the tool being invoked.
    user_id              : Caller's declared identity.
    arguments            : Tool arguments (already type-checked by the guard).
    recent_denial_count  : Number of denied requests from this user in the
                           current sliding window.
    recent_request_count : Total requests from this user in the sliding window.

    Returns
    -------
    RiskResult
    """
    score: float = 0.0
    factors: list[str] = []

    # ── Factor 1: tool risk level ──────────────────────────────────────────────
    if tool == "transfer":
        score += 0.30
        factors.append("Tool 'transfer' carries elevated baseline risk")
    elif tool == "get_balance":
        score += 0.05
        # Low baseline — read-only operation
    else:
        # Unknown tool — scored here only for reporting; the guard already
        # blocks it before risk evaluation in normal flow.
        score += 0.70
        factors.append(f"Tool '{tool}' is not in the allowlist")

    # ── Factor 2: large transfer amount ───────────────────────────────────────
    amount = arguments.get("amount")
    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
        large_threshold = config.MAX_TRANSFER_AMOUNT * config.LARGE_TRANSFER_THRESHOLD
        if amount >= large_threshold:
            fraction = amount / config.MAX_TRANSFER_AMOUNT
            bump = round(0.20 * fraction, 4)
            score += bump
            factors.append(
                f"Transfer amount {amount:.2f} is "
                f"{fraction * 100:.0f}% of the per-call limit"
            )
        # Near-maximum amounts get an extra flag
        if amount >= config.MAX_TRANSFER_AMOUNT * 0.95:
            score += 0.10
            factors.append("Transfer amount is near the maximum allowed limit")

    # ── Factor 3: repeated denial streak ──────────────────────────────────────
    if recent_denial_count >= config.DENIAL_STREAK_ALERT:
        bump = min(0.30, 0.06 * recent_denial_count)
        score += bump
        factors.append(
            f"User '{user_id}' has {recent_denial_count} recent denial(s) "
            f"(threshold: {config.DENIAL_STREAK_ALERT})"
        )
    elif recent_denial_count >= 3:
        score += 0.10
        factors.append(f"User '{user_id}' has {recent_denial_count} recent denials")

    # ── Factor 4: high request velocity ───────────────────────────────────────
    if recent_request_count >= config.RATE_LIMIT_MAX_REQUESTS:
        score += 0.15
        factors.append(
            f"Request rate {recent_request_count} req/window "
            f"(limit: {config.RATE_LIMIT_MAX_REQUESTS})"
        )
    elif recent_request_count >= config.RATE_LIMIT_MAX_REQUESTS * 0.75:
        score += 0.07
        factors.append(
            f"Request rate approaching limit ({recent_request_count}/"
            f"{config.RATE_LIMIT_MAX_REQUESTS})"
        )

    # ── Factor 5: cross-user suspicious pattern ────────────────────────────────
    # Guard already enforces authorization; this flag is informational.
    from_acct = arguments.get("from_account", "")
    to_acct   = arguments.get("to_account", "")
    if from_acct and to_acct and from_acct == to_acct:
        score += 0.15
        factors.append("Source and destination accounts are identical")

    # ── Normalize and build result ─────────────────────────────────────────────
    score = _clamp(score)

    if not factors:
        factors.append("No elevated risk factors detected")

    return RiskResult(
        score=score,
        category=_categorize(score),
        factors=tuple(factors),
        action=_action(score),
    )
