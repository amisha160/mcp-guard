"""
config.py — Centralized configuration for MCP Guard.

All tunable parameters live here. Override via environment variables.
Never put secrets or credentials in this file.
"""

import os

# ── Transfer limits ────────────────────────────────────────────────────────────
MAX_TRANSFER_AMOUNT: float = float(
    os.environ.get("MCP_GUARD_MAX_TRANSFER", "10000")
)

# ── Approval expiry ────────────────────────────────────────────────────────────
APPROVAL_TTL_SECONDS: int = int(
    os.environ.get("MCP_GUARD_APPROVAL_TTL", "300")   # 5 minutes
)

# ── Risk thresholds ────────────────────────────────────────────────────────────
# Requests scoring above RISK_DENY are blocked unconditionally.
# Requests scoring above RISK_REVIEW are queued for approval (transfers always are).
RISK_DENY: float   = float(os.environ.get("MCP_GUARD_RISK_DENY",   "0.85"))
RISK_REVIEW: float = float(os.environ.get("MCP_GUARD_RISK_REVIEW", "0.50"))

# Large-transfer risk threshold (fraction of per-call limit).
# e.g. 0.7 → transfers above 70 % of MAX_TRANSFER_AMOUNT are flagged.
LARGE_TRANSFER_THRESHOLD: float = float(
    os.environ.get("MCP_GUARD_LARGE_XFER_THRESHOLD", "0.70")
)

# ── Abuse / rate-limit ─────────────────────────────────────────────────────────
# Maximum requests per user within the sliding window.
RATE_LIMIT_MAX_REQUESTS: int = int(
    os.environ.get("MCP_GUARD_RATE_LIMIT_MAX", "30")
)
# Sliding window length in seconds.
RATE_LIMIT_WINDOW_SECONDS: int = int(
    os.environ.get("MCP_GUARD_RATE_LIMIT_WINDOW", "60")
)
# How many consecutive denials before a soft-block warning is raised.
DENIAL_STREAK_ALERT: int = int(
    os.environ.get("MCP_GUARD_DENIAL_STREAK", "5")
)

# ── Replay / duplicate-request protection ─────────────────────────────────────
# Maximum age (seconds) for a request_id to be considered a replay.
REPLAY_WINDOW_SECONDS: int = int(
    os.environ.get("MCP_GUARD_REPLAY_WINDOW", "300")
)
# Maximum number of seen request IDs kept in memory.
REPLAY_CACHE_MAX: int = int(
    os.environ.get("MCP_GUARD_REPLAY_CACHE_MAX", "10000")
)

# ── Input size limits ──────────────────────────────────────────────────────────
MAX_USER_ID_LENGTH: int    = int(os.environ.get("MCP_GUARD_MAX_UID_LEN", "128"))
MAX_ACCOUNT_ID_LENGTH: int = int(os.environ.get("MCP_GUARD_MAX_ACCT_LEN", "64"))
MAX_TOOL_NAME_LENGTH: int  = int(os.environ.get("MCP_GUARD_MAX_TOOL_LEN", "64"))

# ── Audit ──────────────────────────────────────────────────────────────────────
AUDIT_LOG_PATH: str = os.environ.get("MCP_GUARD_AUDIT_LOG", "audit.jsonl")
AUDIT_INTEGRITY_PATH: str = os.environ.get(
    "MCP_GUARD_AUDIT_INTEGRITY", "audit_integrity.jsonl"
)

# ── Approvers ─────────────────────────────────────────────────────────────────
# Demo-only stub.  In production replace with a real identity/auth system.
# The string "admin" is NOT authenticated; it is self-declared.
APPROVER_IDS: frozenset = frozenset(
    os.environ.get("MCP_GUARD_APPROVER_IDS", "admin").split(",")
)
