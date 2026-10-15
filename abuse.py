"""
abuse.py — Configurable abuse-prevention layer for MCP Guard.

Provides:
  - Sliding-window rate limiting per user_id.
  - Consecutive-denial streak detection.
  - Replay / duplicate request_id protection.
  - Oversized-input rejection.

All state is in-memory (module-level).  State resets on process restart.
For persistent rate-limit state, replace the dict structures with a Redis
or SQLite backend.

⚠ SIMULATION — thresholds are generous enough not to impede demo usage.
"""

from __future__ import annotations

import collections
import threading
import time
from typing import Any

import config

# ── Thread safety ──────────────────────────────────────────────────────────────
_lock = threading.Lock()

# ── Rate-limit state ───────────────────────────────────────────────────────────
# user_id → deque of UTC timestamps (float) for recent requests
_request_times: dict[str, collections.deque] = collections.defaultdict(
    lambda: collections.deque()
)

# ── Denial-streak state ────────────────────────────────────────────────────────
# user_id → consecutive denial count (reset on any allowed request)
_denial_streak: dict[str, int] = collections.defaultdict(int)

# ── Replay cache ───────────────────────────────────────────────────────────────
# request_id → first-seen timestamp
_seen_ids: dict[str, float] = {}
# Ordered queue to evict expired entries
_seen_ids_order: collections.deque = collections.deque()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> float:
    return time.monotonic()


def _real_now() -> float:
    """Wall-clock time for eviction comparisons (monotonic is safer for intervals)."""
    return time.monotonic()


def _purge_old_times(dq: collections.deque, window: float, now: float) -> None:
    """Remove timestamps older than `window` seconds from a deque."""
    while dq and (now - dq[0]) > window:
        dq.popleft()


def _evict_old_replay_ids(now: float) -> None:
    """Remove replay-cache entries that have aged out."""
    while _seen_ids_order:
        rid, ts = _seen_ids_order[0]
        if (now - ts) > config.REPLAY_WINDOW_SECONDS:
            _seen_ids_order.popleft()
            _seen_ids.pop(rid, None)
        else:
            break
    # Hard cap to prevent unbounded growth
    while len(_seen_ids) > config.REPLAY_CACHE_MAX:
        if _seen_ids_order:
            rid, _ = _seen_ids_order.popleft()
            _seen_ids.pop(rid, None)
        else:
            break


# ── Public API ─────────────────────────────────────────────────────────────────

class AbuseViolation(Exception):
    """Raised when an abuse check fails.  `args[0]` is the denial reason."""


def check_input_sizes(
    *,
    user_id: Any,
    tool: Any,
    account_id: str | None = None,
) -> None:
    """
    Reject inputs that exceed configured length limits.

    Raises AbuseViolation if any value is too long.
    Does NOT check types — the guard handles that before calling here.
    """
    if isinstance(user_id, str) and len(user_id) > config.MAX_USER_ID_LENGTH:
        raise AbuseViolation(
            f"user_id exceeds maximum length ({config.MAX_USER_ID_LENGTH})"
        )
    if isinstance(tool, str) and len(tool) > config.MAX_TOOL_NAME_LENGTH:
        raise AbuseViolation(
            f"tool name exceeds maximum length ({config.MAX_TOOL_NAME_LENGTH})"
        )
    if (
        account_id is not None
        and isinstance(account_id, str)
        and len(account_id) > config.MAX_ACCOUNT_ID_LENGTH
    ):
        raise AbuseViolation(
            f"account_id exceeds maximum length ({config.MAX_ACCOUNT_ID_LENGTH})"
        )


def check_replay(request_id: str | None) -> None:
    """
    Detect duplicate request IDs within the replay window.

    If `request_id` is None or empty the check is skipped (idempotency keys
    are optional in this prototype).

    Raises AbuseViolation for replayed IDs.
    """
    if not request_id:
        return

    now = _real_now()
    with _lock:
        _evict_old_replay_ids(now)
        if request_id in _seen_ids:
            raise AbuseViolation(
                f"Duplicate request_id '{request_id}' (replay detected)"
            )
        _seen_ids[request_id] = now
        _seen_ids_order.append((request_id, now))


def check_rate_limit(user_id: str) -> int:
    """
    Enforce per-user sliding-window rate limit.

    Records this request regardless of outcome.
    Returns the current request count within the window.

    Raises AbuseViolation if the limit is exceeded.
    """
    now = _real_now()
    with _lock:
        dq = _request_times[user_id]
        _purge_old_times(dq, config.RATE_LIMIT_WINDOW_SECONDS, now)
        count = len(dq)
        if count >= config.RATE_LIMIT_MAX_REQUESTS:
            raise AbuseViolation(
                f"Rate limit exceeded for user '{user_id}': "
                f"{count} requests in {config.RATE_LIMIT_WINDOW_SECONDS}s window "
                f"(max {config.RATE_LIMIT_MAX_REQUESTS})"
            )
        dq.append(now)
        return count + 1


def record_outcome(user_id: str, *, allowed: bool) -> int:
    """
    Update the denial streak counter and return the current streak.

    Call AFTER the guard makes its authorization decision.
    """
    with _lock:
        if allowed:
            _denial_streak[user_id] = 0
        else:
            _denial_streak[user_id] += 1
        return _denial_streak[user_id]


def get_denial_streak(user_id: str) -> int:
    """Return the current denial streak for a user (thread-safe read)."""
    with _lock:
        return _denial_streak.get(user_id, 0)


def get_request_count(user_id: str) -> int:
    """Return the number of requests from user_id in the current window."""
    now = _real_now()
    with _lock:
        dq = _request_times[user_id]
        _purge_old_times(dq, config.RATE_LIMIT_WINDOW_SECONDS, now)
        return len(dq)


def reset_user(user_id: str) -> None:
    """
    Clear all abuse-tracking state for a user.

    Useful in tests to avoid cross-test contamination.
    """
    with _lock:
        _request_times.pop(user_id, None)
        _denial_streak.pop(user_id, None)


def reset_all() -> None:
    """Clear all in-memory abuse state.  Intended for test teardown."""
    with _lock:
        _request_times.clear()
        _denial_streak.clear()
        _seen_ids.clear()
        _seen_ids_order.clear()
