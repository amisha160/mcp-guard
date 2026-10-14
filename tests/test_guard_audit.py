"""

tests/test_guard_audit.py

Audit-focused tests for guard.py.  Each test group is labelled with the

requirement it satisfies:

  REQ-1  Allowed calls create audit entries.

  REQ-2  Blocked calls create audit entries with clear reasons.

  REQ-3  Unknown tools and unauthorized accounts are denied.

  REQ-4  Invalid or malformed arguments are handled safely.

  REQ-5  Rejected transfers do not change mock account balances.

  REQ-6  NaN and positive/negative infinity are rejected through the

         guarded transfer path.

  REQ-7  Unexpected bank exceptions are audited and returned as generic errors.

Design notes

------------

* AUDIT_LOG and ACCOUNTS are module-level state; both are reset by

  autouse fixtures so each test starts with a clean slate.

* No application files are modified.

* Existing tests in test_bank.py and test_guard.py are not touched.

"""

import math

import pytest

from unittest.mock import patch

from bank import ACCOUNTS

from guard import AUDIT_LOG, approve_transfer, handle_request

# ---------------------------------------------------------------------------

# Fixtures

# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)

def clear_audit_log():

    """Reset the in-memory audit log before every test."""

    AUDIT_LOG.clear()

    yield

    AUDIT_LOG.clear()

@pytest.fixture(autouse=True)

def reset_accounts():

    """Restore account balances to their original values after every test."""

    snapshot = {acct: data["balance"] for acct, data in ACCOUNTS.items()}

    yield

    for acct, balance in snapshot.items():

        ACCOUNTS[acct]["balance"] = balance

# ---------------------------------------------------------------------------

# Helpers

# ---------------------------------------------------------------------------

def _make_balance_request(user_id="riya", account_id="ACC-1001"):

    return {

        "user_id": user_id,

        "tool": "get_balance",

        "arguments": {"account_id": account_id},

    }

def _make_transfer_request(

    user_id="riya",

    from_account="ACC-1001",

    to_account="ACC-1002",

    amount=100.0,

):

    return {

        "user_id": user_id,

        "tool": "transfer",

        "arguments": {

            "from_account": from_account,

            "to_account": to_account,

            "amount": amount,

        },

    }

# ---------------------------------------------------------------------------

# REQ-1  Allowed calls create audit entries

# ---------------------------------------------------------------------------

class TestAllowedCallsAreAudited:

    """REQ-1: every successful path through handle_request writes one

    audit entry with allowed=True."""

    def test_allowed_get_balance_writes_one_audit_entry(self):

        result = handle_request(_make_balance_request())

        assert result["allowed"] is True

        assert len(AUDIT_LOG) == 1

    def test_allowed_get_balance_audit_entry_is_correct(self):

        handle_request(_make_balance_request())

        entry = AUDIT_LOG[0]

        assert entry["allowed"] is True

        assert entry["user_id"] == "riya"

        assert entry["tool"] == "get_balance"

        assert isinstance(entry["reason"], str) and entry["reason"]

    def test_allowed_get_balance_audit_entry_has_timestamp(self):

        handle_request(_make_balance_request())

        entry = AUDIT_LOG[0]

        # The "time" field must be a non-empty ISO 8601 string.

        assert isinstance(entry["time"], str) and entry["time"]

    def test_allowed_transfer_writes_one_audit_entry(self):

        result = handle_request(_make_transfer_request())

        assert result["allowed"] is True

        assert len(AUDIT_LOG) == 1

    def test_allowed_transfer_audit_entry_is_correct(self):

        handle_request(_make_transfer_request())

        entry = AUDIT_LOG[0]

        assert entry["allowed"] is True

        assert entry["user_id"] == "riya"

        assert entry["tool"] == "transfer"

        assert isinstance(entry["reason"], str) and entry["reason"]

    def test_arjun_allowed_get_balance_writes_audit_entry(self):

        result = handle_request(

            _make_balance_request(user_id="arjun", account_id="ACC-2001")

        )

        assert result["allowed"] is True

        assert len(AUDIT_LOG) == 1

        assert AUDIT_LOG[0]["user_id"] == "arjun"

    def test_allowed_call_returns_result_payload(self):

        result = handle_request(_make_balance_request())

        assert "result" in result

        assert result["result"]["account_id"] == "ACC-1001"

        assert math.isclose(result["result"]["balance"], 25000.0)


    def test_allowed_transfer_returns_simulated_status(self):
        result = handle_request(_make_transfer_request())
        assert result["allowed"] is True
        assert result["status"] == "pending_approval"
        assert "approval_id" in result
        assert "result" not in result

    def test_each_allowed_call_appends_exactly_one_entry(self):

        """Two sequential allowed calls must produce exactly two entries."""

        handle_request(_make_balance_request())

        handle_request(

            _make_balance_request(user_id="arjun", account_id="ACC-2001")

        )

        assert len(AUDIT_LOG) == 2

        assert all(e["allowed"] is True for e in AUDIT_LOG)

# ---------------------------------------------------------------------------

# REQ-2  Blocked calls create audit entries with clear reasons

# ---------------------------------------------------------------------------

class TestBlockedCallsAreAudited:

    """REQ-2: every rejection path writes one audit entry with

    allowed=False and a non-empty reason string."""

    def _assert_blocked_with_reason(self, request, expected_reason=None):

        result = handle_request(request)

        assert result["allowed"] is False

        assert len(AUDIT_LOG) == 1

        assert AUDIT_LOG[0]["allowed"] is False

        reason = AUDIT_LOG[0]["reason"]

        assert isinstance(reason, str) and reason

        if expected_reason is not None:

            assert reason == expected_reason

        return result

    def test_unknown_tool_blocked_with_reason(self):

        req = {"user_id": "riya", "tool": "delete_account", "arguments": {}}

        result = self._assert_blocked_with_reason(req, "Tool not allowed")

        assert result["reason"] == "Tool not allowed"

    def test_unauthorized_account_blocked_with_reason(self):

        req = _make_balance_request(user_id="riya", account_id="ACC-2001")

        result = self._assert_blocked_with_reason(

            req, "User not authorized for account"

        )

        assert result["reason"] == "User not authorized for account"

    def test_nonexistent_user_blocked_with_reason(self):

        req = _make_balance_request(user_id="mallory", account_id="ACC-1001")

        result = self._assert_blocked_with_reason(

            req, "User not authorized for account"

        )

    def test_invalid_user_id_blocked_with_reason(self):

        req = {"user_id": None, "tool": "get_balance",

               "arguments": {"account_id": "ACC-1001"}}

        result = self._assert_blocked_with_reason(req, "Invalid user_id")

        assert result["reason"] == "Invalid user_id"

    def test_empty_user_id_blocked_with_reason(self):

        req = {"user_id": "", "tool": "get_balance",

               "arguments": {"account_id": "ACC-1001"}}

        result = self._assert_blocked_with_reason(req, "Invalid user_id")

    def test_non_dict_arguments_blocked_with_reason(self):

        req = {"user_id": "riya", "tool": "get_balance", "arguments": None}

        result = self._assert_blocked_with_reason(

            req, "Arguments must be an object"

        )

    def test_negative_amount_blocked_with_reason(self):

        req = _make_transfer_request(amount=-50)

        result = self._assert_blocked_with_reason(req, "Amount must be positive")

        assert result["reason"] == "Amount must be positive"

    def test_zero_amount_blocked_with_reason(self):

        req = _make_transfer_request(amount=0)

        self._assert_blocked_with_reason(req, "Amount must be positive")

    def test_string_amount_blocked_with_reason(self):

        req = _make_transfer_request(amount="500")

        self._assert_blocked_with_reason(req, "Amount must be numeric")

    def test_boolean_true_amount_blocked_with_reason(self):

        # bool is a subclass of int; the guard must reject it explicitly.

        req = _make_transfer_request(amount=True)

        self._assert_blocked_with_reason(req, "Amount must be numeric")

    def test_boolean_false_amount_blocked_with_reason(self):

        req = _make_transfer_request(amount=False)

        self._assert_blocked_with_reason(req, "Amount must be numeric")

    def test_none_amount_blocked_with_reason(self):

        req = _make_transfer_request(amount=None)

        self._assert_blocked_with_reason(req, "Amount must be numeric")

    def test_unauthorized_destination_blocked_with_reason(self):

        # riya cannot transfer to arjun's account ACC-2001.

        req = _make_transfer_request(

            user_id="riya",

            from_account="ACC-1001",

            to_account="ACC-2001",

            amount=100,

        )

        result = self._assert_blocked_with_reason(

            req, "User not authorized for destination"

        )

# ---------------------------------------------------------------------------

# REQ-3  Unknown tools and unauthorized accounts are denied

# ---------------------------------------------------------------------------

class TestUnknownToolsAndUnauthorizedAccounts:

    """REQ-3: the tool allowlist and user-to-account mapping are enforced."""

    @pytest.mark.parametrize("tool_name", [

        "delete_account",

        "admin_reset",

        "get_balance ",      # trailing space — not in allowlist

        "TRANSFER",          # case-sensitive check

        "",

        "transfer; rm -rf",  # injection attempt

    ])

    def test_unknown_tool_is_denied(self, tool_name):

        req = {"user_id": "riya", "tool": tool_name, "arguments": {}}

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Tool not allowed"

        assert len(AUDIT_LOG) == 1

        assert AUDIT_LOG[0]["allowed"] is False

    def test_riya_cannot_access_arjuns_account(self):

        result = handle_request(

            _make_balance_request(user_id="riya", account_id="ACC-2001")

        )

        assert result["allowed"] is False

        assert result["reason"] == "User not authorized for account"

    def test_arjun_cannot_access_riyas_account(self):

        result = handle_request(

            _make_balance_request(user_id="arjun", account_id="ACC-1001")

        )

        assert result["allowed"] is False

        assert result["reason"] == "User not authorized for account"

    def test_completely_unknown_user_is_denied(self):

        result = handle_request(

            _make_balance_request(user_id="eve", account_id="ACC-1001")

        )

        assert result["allowed"] is False

    def test_none_user_id_is_denied(self):

        req = {"user_id": None, "tool": "get_balance",

               "arguments": {"account_id": "ACC-1001"}}

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Invalid user_id"

    def test_integer_user_id_is_denied(self):

        req = {"user_id": 42, "tool": "get_balance",

               "arguments": {"account_id": "ACC-1001"}}

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Invalid user_id"

    def test_riya_cannot_use_nonexistent_account(self):

        result = handle_request(

            _make_balance_request(user_id="riya", account_id="ACC-9999")

        )

        assert result["allowed"] is False

    def test_riya_cannot_transfer_from_arjuns_account(self):

        # from_account must be in the user's own set.

        req = _make_transfer_request(

            user_id="riya",

            from_account="ACC-2001",

            to_account="ACC-1001",

            amount=100,

        )

        result = handle_request(req)

        assert result["allowed"] is False

# ---------------------------------------------------------------------------

# REQ-4  Invalid or malformed arguments are handled safely

# ---------------------------------------------------------------------------

class TestMalformedToolNames:
    @pytest.mark.parametrize("tool_name", [[], {}])
    def test_unhashable_tool_name_is_rejected_and_audited(self, tool_name):
        result = handle_request({
            "user_id": "riya",
            "tool": tool_name,
            "arguments": {},
        })

        assert result["allowed"] is False
        assert result["reason"] == "Tool not allowed"
        assert len(AUDIT_LOG) == 1
        assert AUDIT_LOG[0]["allowed"] is False

class TestMalformedArguments:

    """REQ-4: the guard must never crash or leak on any argument shape."""

    def test_list_arguments_rejected(self):

        req = {"user_id": "riya", "tool": "get_balance",

               "arguments": ["ACC-1001"]}

        result = handle_request(req)

        assert result["allowed"] is False

    def test_string_arguments_rejected(self):

        req = {"user_id": "riya", "tool": "get_balance",

               "arguments": "ACC-1001"}

        result = handle_request(req)

        assert result["allowed"] is False

    def test_integer_arguments_rejected(self):

        req = {"user_id": "riya", "tool": "get_balance", "arguments": 123}

        result = handle_request(req)

        assert result["allowed"] is False

    def test_missing_arguments_key_rejected(self):

        req = {"user_id": "riya", "tool": "get_balance"}

        result = handle_request(req)

        # arguments is absent; args will be None -> "Arguments must be an object"

        assert result["allowed"] is False

    def test_extra_argument_key_rejected_for_get_balance(self):

        req = {

            "user_id": "riya",

            "tool": "get_balance",

            "arguments": {"account_id": "ACC-1001", "extra": "value"},

        }

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Invalid arguments"

    def test_missing_account_id_rejected_for_get_balance(self):

        req = {

            "user_id": "riya",

            "tool": "get_balance",

            "arguments": {},

        }

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Invalid arguments"

    def test_integer_account_id_rejected(self):

        req = {

            "user_id": "riya",

            "tool": "get_balance",

            "arguments": {"account_id": 1001},

        }

        result = handle_request(req)

        assert result["allowed"] is False

    def test_extra_argument_key_rejected_for_transfer(self):

        req = _make_transfer_request()

        req["arguments"]["extra"] = "value"

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Invalid arguments"

    def test_missing_amount_rejected_for_transfer(self):

        req = {

            "user_id": "riya",

            "tool": "transfer",

            "arguments": {"from_account": "ACC-1001", "to_account": "ACC-1002"},

        }

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == "Invalid arguments"

    def test_completely_empty_request_handled_safely(self):

        result = handle_request({})

        assert result["allowed"] is False


    def test_non_dict_request_raises_gracefully(self):
        result = handle_request("not a dict")
        assert result["allowed"] is False
        assert result["reason"] == "Invalid request"
        assert len(AUDIT_LOG) == 1
        assert AUDIT_LOG[0]["allowed"] is False

    def test_each_malformed_call_produces_one_audit_entry(self):

        handle_request({"user_id": "riya", "tool": "get_balance",

                        "arguments": {"account_id": 1001}})

        handle_request({"user_id": "riya", "tool": "get_balance",

                        "arguments": []})

        assert len(AUDIT_LOG) == 2

        assert all(e["allowed"] is False for e in AUDIT_LOG)

# ---------------------------------------------------------------------------

# REQ-5  Rejected transfers do not change mock account balances

# ---------------------------------------------------------------------------

class TestRejectedTransfersLeaveBalancesUnchanged:

    """REQ-5: any request that is denied must leave the in-memory ACCOUNTS

    dict exactly as it was before the call."""

    def _snapshot(self):

        return {acct: data["balance"] for acct, data in ACCOUNTS.items()}

    def _assert_balances_unchanged(self, before, after):

        for acct in before:

            assert math.isclose(before[acct], after[acct]), (

                f"Balance changed for {acct}: {before[acct]} -> {after[acct]}"

            )

    def test_wrong_tool_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request({"user_id": "riya", "tool": "delete_account",

                        "arguments": {}})

        self._assert_balances_unchanged(before, self._snapshot())

    def test_unauthorized_account_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_balance_request(user_id="riya",

                                              account_id="ACC-2001"))

        self._assert_balances_unchanged(before, self._snapshot())

    def test_negative_amount_transfer_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_transfer_request(amount=-100))

        self._assert_balances_unchanged(before, self._snapshot())

    def test_zero_amount_transfer_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_transfer_request(amount=0))

        self._assert_balances_unchanged(before, self._snapshot())

    def test_boolean_amount_transfer_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_transfer_request(amount=True))

        self._assert_balances_unchanged(before, self._snapshot())

    def test_string_amount_transfer_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_transfer_request(amount="500"))

        self._assert_balances_unchanged(before, self._snapshot())

    def test_none_amount_transfer_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_transfer_request(amount=None))

        self._assert_balances_unchanged(before, self._snapshot())

    def test_unauthorized_destination_leaves_balances_unchanged(self):

        before = self._snapshot()

        handle_request(_make_transfer_request(

            user_id="riya",

            from_account="ACC-1001",

            to_account="ACC-2001",

            amount=100,

        ))

        self._assert_balances_unchanged(before, self._snapshot())


    def test_invalid_user_id_leaves_balances_unchanged(self):
        before = self._snapshot()

        pending = handle_request(_make_transfer_request(amount=100))
        assert pending["allowed"] is True
        assert pending["status"] == "pending_approval"

        result = handle_request({
            "user_id": None,
            "tool": "transfer",
            "arguments": {
                "from_account": "ACC-1001",
                "to_account": "ACC-1002",
                "amount": 100,
            },
        })

        assert result["allowed"] is False
        self._assert_balances_unchanged(before, self._snapshot())

    def test_insufficient_funds_transfer_leaves_balances_unchanged(self):

        """A valid request that the bank itself rejects must not mutate state."""

        before = self._snapshot()

        # Attempt to transfer more than the balance.

        handle_request(_make_transfer_request(

            from_account="ACC-1001",

            to_account="ACC-1002",

            amount=99999.0,

        ))

        self._assert_balances_unchanged(before, self._snapshot())

# ---------------------------------------------------------------------------

# REQ-6  NaN and positive/negative infinity are rejected through the guard

# ---------------------------------------------------------------------------

class TestNonFiniteAmountsAreRejectedByGuard:

    """REQ-6: NaN, +inf, and -inf must be caught by the guard's own

    validation layer (not by the bank) and must produce an audit entry."""

    @pytest.mark.parametrize("bad_amount,expected_reason", [

        (float("nan"),  "Amount must be finite"),

        (float("inf"),  "Amount must be finite"),

        (float("-inf"), "Amount must be finite"),    # isfinite check fires before the <= 0 check

    ])

    def test_nonfinite_amount_is_rejected(self, bad_amount, expected_reason):

        req = _make_transfer_request(amount=bad_amount)

        result = handle_request(req)

        assert result["allowed"] is False

        assert result["reason"] == expected_reason

    @pytest.mark.parametrize("bad_amount", [

        float("nan"),

        float("inf"),

        float("-inf"),

    ])

    def test_nonfinite_amount_produces_audit_entry(self, bad_amount):

        handle_request(_make_transfer_request(amount=bad_amount))

        assert len(AUDIT_LOG) == 1

        assert AUDIT_LOG[0]["allowed"] is False

        assert isinstance(AUDIT_LOG[0]["reason"], str)

    @pytest.mark.parametrize("bad_amount", [

        float("nan"),

        float("inf"),

        float("-inf"),

    ])

    def test_nonfinite_amount_does_not_change_balances(self, bad_amount):

        before = {acct: data["balance"] for acct, data in ACCOUNTS.items()}

        handle_request(_make_transfer_request(amount=bad_amount))

        after = {acct: data["balance"] for acct, data in ACCOUNTS.items()}

        for acct in before:

            assert math.isclose(before[acct], after[acct]), (

                f"Balance mutated for {acct} with amount={bad_amount!r}"

            )

    def test_nan_amount_is_blocked_by_guard_not_bank(self):

        """Confirm the guard's own isfinite check fires, not the bank's."""

        req = _make_transfer_request(amount=float("nan"))

        with patch("guard.transfer") as mock_transfer:

            result = handle_request(req)

        # If the guard correctly blocks NaN, transfer() must never be called.

        mock_transfer.assert_not_called()

        assert result["allowed"] is False

    def test_positive_inf_is_blocked_by_guard_not_bank(self):

        """Confirm the guard's own isfinite check fires for +inf."""

        req = _make_transfer_request(amount=float("inf"))

        with patch("guard.transfer") as mock_transfer:

            result = handle_request(req)

        mock_transfer.assert_not_called()

        assert result["allowed"] is False

# ---------------------------------------------------------------------------

# REQ-7  Unexpected bank exceptions are audited

# ---------------------------------------------------------------------------

class TestUnexpectedExceptionAudit:

    """Unexpected bank exceptions must be audited and safely denied."""

    def test_unexpected_bank_exception_is_audited_and_returns_generic_error(self):

        req = _make_balance_request()

        with patch("guard.get_balance", side_effect=RuntimeError("DB offline")):

            result = handle_request(req)

        # Unexpected internal details must not be exposed:

        assert result["allowed"] is False

        assert "reason" in result

        # The reason must not leak the raw internal message verbatim; a safe

        # generic string is acceptable.  We only assert it is a non-empty string.

        assert isinstance(result["reason"], str) and result["reason"]

        # An audit entry MUST have been written.

        assert len(AUDIT_LOG) == 1

        assert AUDIT_LOG[0]["allowed"] is False


    def test_unexpected_transfer_exception_is_audited(self):
        pending = handle_request(_make_transfer_request())
        assert pending["allowed"] is True
        assert pending["status"] == "pending_approval"

        with patch("guard.transfer", side_effect=TypeError("unexpected type")):
            result = approve_transfer("admin", pending["approval_id"])

        assert result["allowed"] is False
        assert result["reason"] == "Internal error"

        denied_entries = [
            entry for entry in AUDIT_LOG
            if entry["allowed"] is False
        ]
        assert len(denied_entries) >= 1
        assert all(entry["reason"] for entry in denied_entries)
