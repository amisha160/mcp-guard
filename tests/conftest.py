"""
tests/conftest.py — Shared pytest fixtures for MCP Guard test suite.

These fixtures ensure that module-level state in guard, abuse, and bank
is fully reset between tests, preventing cross-test contamination.
"""

import pytest

import abuse
import guard
from bank import ACCOUNTS


@pytest.fixture(autouse=True)
def reset_guard_state():
    """
    Reset all module-level guard and abuse state before every test.

    This covers:
      - AUDIT_LOG      — in-memory audit entries
      - PENDING_APPROVALS — queued transfers
      - abuse tracking — rate-limit counters, denial streaks, replay cache
      - ACCOUNTS       — restore original balances
    """
    # Snapshot original balances
    original_balances = {
        acct: data["balance"] for acct, data in ACCOUNTS.items()
    }

    # Clean state before test
    guard.AUDIT_LOG.clear()
    guard.PENDING_APPROVALS.clear()
    abuse.reset_all()

    yield

    # Clean state after test
    guard.AUDIT_LOG.clear()
    guard.PENDING_APPROVALS.clear()
    abuse.reset_all()

    # Restore balances
    for acct, balance in original_balances.items():
        ACCOUNTS[acct]["balance"] = balance
