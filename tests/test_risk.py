"""
tests/test_risk.py — Unit tests for risk.py.

Covers:
  - Baseline scores for each tool.
  - Large-transfer risk factor.
  - Denial-streak risk factor.
  - High-velocity risk factor.
  - Same-account transfer flag.
  - Score clamping at 1.0.
  - Category and action derivation.
  - Determinism — same inputs → same output.
  - RiskResult.to_dict() shape.
"""

import pytest

import config
from risk import RiskResult, evaluate


# ── Helpers ────────────────────────────────────────────────────────────────────

def _balance_risk(**kwargs) -> RiskResult:
    defaults = dict(
        tool="get_balance",
        user_id="riya",
        arguments={"account_id": "ACC-1001"},
    )
    defaults.update(kwargs)
    return evaluate(**defaults)


def _transfer_risk(amount: float = 100.0, **kwargs) -> RiskResult:
    defaults = dict(
        tool="transfer",
        user_id="riya",
        arguments={
            "from_account": "ACC-1001",
            "to_account": "ACC-1002",
            "amount": amount,
        },
    )
    defaults.update(kwargs)
    return evaluate(**defaults)


# ── Basic scores ───────────────────────────────────────────────────────────────

class TestBaselineScores:
    def test_get_balance_has_low_baseline(self):
        r = _balance_risk()
        assert r.score < config.RISK_REVIEW, (
            f"get_balance score {r.score} should be < RISK_REVIEW {config.RISK_REVIEW}"
        )

    def test_small_transfer_has_medium_or_lower_score(self):
        r = _transfer_risk(amount=100.0)
        # Small transfer should not hit DENY threshold
        assert r.score < config.RISK_DENY

    def test_get_balance_action_is_allow(self):
        r = _balance_risk()
        assert r.action == "allow"

    def test_small_transfer_action_is_not_deny(self):
        r = _transfer_risk(amount=100.0)
        assert r.action in ("allow", "review")


# ── Large transfer ─────────────────────────────────────────────────────────────

class TestLargeTransfer:
    def test_transfer_at_large_threshold_raises_score(self):
        threshold = config.MAX_TRANSFER_AMOUNT * config.LARGE_TRANSFER_THRESHOLD
        r_small = _transfer_risk(amount=threshold * 0.5)
        r_large = _transfer_risk(amount=threshold)
        assert r_large.score > r_small.score

    def test_near_maximum_transfer_has_extra_factor(self):
        near_max = config.MAX_TRANSFER_AMOUNT * 0.96
        r = _transfer_risk(amount=near_max)
        factor_text = " ".join(r.factors)
        assert "near the maximum" in factor_text.lower() or r.score >= 0.50

    def test_large_transfer_factor_is_in_factors_list(self):
        large = config.MAX_TRANSFER_AMOUNT * config.LARGE_TRANSFER_THRESHOLD
        r = _transfer_risk(amount=large)
        assert any("limit" in f.lower() or "%" in f for f in r.factors)

    def test_large_transfer_score_is_in_0_to_1(self):
        r = _transfer_risk(amount=config.MAX_TRANSFER_AMOUNT)
        assert 0.0 <= r.score <= 1.0


# ── Denial streak ──────────────────────────────────────────────────────────────

class TestDenialStreak:
    def test_denial_streak_raises_score(self):
        r_clean = _balance_risk(recent_denial_count=0)
        r_streak = _balance_risk(recent_denial_count=config.DENIAL_STREAK_ALERT)
        assert r_streak.score > r_clean.score

    def test_denial_streak_factor_named_in_output(self):
        r = _balance_risk(recent_denial_count=config.DENIAL_STREAK_ALERT)
        factor_text = " ".join(r.factors)
        assert "denial" in factor_text.lower()

    def test_small_denial_count_below_alert_raises_score_slightly(self):
        r0 = _balance_risk(recent_denial_count=0)
        r3 = _balance_risk(recent_denial_count=3)
        assert r3.score > r0.score

    def test_high_denial_streak_does_not_exceed_1(self):
        r = _balance_risk(recent_denial_count=100)
        assert r.score <= 1.0


# ── Request velocity ───────────────────────────────────────────────────────────

class TestRequestVelocity:
    def test_high_velocity_raises_score(self):
        r_normal = _balance_risk(recent_request_count=1)
        r_fast   = _balance_risk(
            recent_request_count=config.RATE_LIMIT_MAX_REQUESTS + 1
        )
        assert r_fast.score > r_normal.score

    def test_near_limit_velocity_raises_score(self):
        near = int(config.RATE_LIMIT_MAX_REQUESTS * 0.80)
        r_normal = _balance_risk(recent_request_count=1)
        r_near   = _balance_risk(recent_request_count=near)
        assert r_near.score > r_normal.score

    def test_velocity_factor_named_in_output(self):
        r = _balance_risk(
            recent_request_count=config.RATE_LIMIT_MAX_REQUESTS + 5
        )
        factor_text = " ".join(r.factors)
        assert "rate" in factor_text.lower() or "request" in factor_text.lower()


# ── Same-account pattern ───────────────────────────────────────────────────────

class TestSameAccountPattern:
    def test_same_source_destination_raises_score(self):
        r_diff = evaluate(
            tool="transfer",
            user_id="riya",
            arguments={
                "from_account": "ACC-1001",
                "to_account":   "ACC-1002",
                "amount":       100.0,
            },
        )
        r_same = evaluate(
            tool="transfer",
            user_id="riya",
            arguments={
                "from_account": "ACC-1001",
                "to_account":   "ACC-1001",
                "amount":       100.0,
            },
        )
        assert r_same.score > r_diff.score

    def test_same_account_factor_appears(self):
        r = evaluate(
            tool="transfer",
            user_id="riya",
            arguments={
                "from_account": "ACC-1001",
                "to_account":   "ACC-1001",
                "amount":       100.0,
            },
        )
        assert any("identical" in f.lower() for f in r.factors)


# ── Determinism ────────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_inputs_produce_same_score(self):
        r1 = _transfer_risk(amount=5000.0, recent_denial_count=2)
        r2 = _transfer_risk(amount=5000.0, recent_denial_count=2)
        assert r1.score == r2.score
        assert r1.category == r2.category
        assert r1.action == r2.action

    def test_same_inputs_produce_same_factors(self):
        r1 = _transfer_risk(amount=8000.0, recent_denial_count=4)
        r2 = _transfer_risk(amount=8000.0, recent_denial_count=4)
        assert r1.factors == r2.factors


# ── Category and action derivation ────────────────────────────────────────────

class TestCategoryAndAction:
    @pytest.mark.parametrize("score,expected_cat", [
        (0.10, "low"),
        (0.30, "medium"),
        (config.RISK_REVIEW + 0.01, "high"),
        (config.RISK_DENY + 0.01,   "critical"),
    ])
    def test_category_matches_score(self, score, expected_cat):
        # We cannot directly inject a score, so construct a scenario that
        # produces approximately the right score and verify the category logic
        # independently using the internal helpers.
        from risk import _categorize
        assert _categorize(score) == expected_cat

    @pytest.mark.parametrize("score,expected_action", [
        (0.10, "allow"),
        (config.RISK_REVIEW + 0.01, "review"),
        (config.RISK_DENY + 0.01,   "deny"),
    ])
    def test_action_matches_score(self, score, expected_action):
        from risk import _action
        assert _action(score) == expected_action


# ── to_dict() shape ────────────────────────────────────────────────────────────

class TestToDictShape:
    def test_to_dict_contains_required_keys(self):
        r = _balance_risk()
        d = r.to_dict()
        assert set(d.keys()) >= {"score", "category", "factors", "action"}

    def test_to_dict_score_is_float(self):
        r = _balance_risk()
        assert isinstance(r.to_dict()["score"], float)

    def test_to_dict_factors_is_list(self):
        r = _balance_risk()
        assert isinstance(r.to_dict()["factors"], list)

    def test_to_dict_category_is_string(self):
        r = _balance_risk()
        assert isinstance(r.to_dict()["category"], str)

    def test_to_dict_action_is_valid(self):
        r = _balance_risk()
        assert r.to_dict()["action"] in ("allow", "review", "deny")

    def test_factors_never_empty(self):
        r = _balance_risk()
        assert len(r.factors) >= 1
