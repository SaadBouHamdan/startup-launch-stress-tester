import pytest

from agents.risk_reviewer import risk_reviewer
from state import StartupState


@pytest.mark.parametrize("max_price", [None, 9.0, 8.0])
def test_risk_reviewer_allows_price_within_cap(max_price):
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=8,
        proposed_sales=100,
        break_even_sales=75,
        expected_profit=100,
        max_price=max_price,
    )

    assert risk_reviewer(state) == {"risks": [], "approved": True}


def test_risk_reviewer_rejects_price_above_cap():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=8,
        proposed_sales=100,
        break_even_sales=75,
        expected_profit=100,
        max_price=7,
    )

    assert risk_reviewer(state) == {
        "risks": [
            "Proposed price 8.0 exceeds max_price 7.0. "
            "Lower the proposed price to 7.0 or less."
        ],
        "approved": False,
    }


@pytest.mark.parametrize("max_price", [float("nan"), float("inf"), float("-inf")])
def test_risk_reviewer_reports_nonfinite_cap(max_price):
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=8,
        proposed_sales=100,
        break_even_sales=75,
        expected_profit=100,
        max_price=max_price,
    )

    assert risk_reviewer(state) == {
        "risks": ["max_price must be a valid finite number."],
        "approved": False,
    }


def test_risk_reviewer_approves_passing_plan():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=8,
        proposed_sales=100,
        break_even_sales=75,
        expected_profit=100,
        constraints=[],
        risks=["A risk from a previous review"],
        revision_count=1,
    )
    original_state = state.model_dump()

    result = risk_reviewer(state)

    assert result == {"risks": [], "approved": True}
    assert state.model_dump() == original_state


def test_risk_reviewer_rejects_failing_financial_plan():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=6,
        proposed_sales=80,
        break_even_sales=150,
        expected_profit=-140,
        constraints=[],
    )
    original_state = state.model_dump()

    result = risk_reviewer(state)

    assert result["approved"] is False
    assert "Expected profit is negative." in result["risks"]
    assert "Proposed sales are below break-even sales." in result["risks"]
    assert state.model_dump() == original_state


def test_risk_reviewer_requires_manual_constraint_verification():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=8,
        proposed_sales=100,
        break_even_sales=75,
        expected_profit=100,
        constraints=["Do not sell on campus"],
    )
    original_state = state.model_dump()

    result = risk_reviewer(state)

    assert result["approved"] is False
    assert (
        "Constraint requires manual verification: Do not sell on campus"
        in result["risks"]
    )
    assert state.model_dump() == original_state


def test_risk_reviewer_reports_missing_financial_values():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=None,
        proposed_sales=None,
        break_even_sales=None,
        expected_profit=None,
    )
    original_state = state.model_dump()

    result = risk_reviewer(state)

    assert result == {
        "risks": [
            "Missing required field: expected_profit.",
            "Missing required field: break_even_sales.",
            "Missing required field: proposed_sales.",
            "Missing required field: proposed_price.",
        ],
        "approved": False,
    }
    assert state.model_dump() == original_state


def test_unpriced_paid_action_blocks_approval():
    state = StartupState(
        startup_idea="Printed mugs",
        selling_price=12,
        cost_per_sale=5,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=12,
        proposed_sales=80,
        break_even_sales=43,
        expected_profit=260,
        unpriced_paid_actions=["Paid ads"],
    )

    assert risk_reviewer(state) == {
        "risks": ["Paid action needs a cost estimate: Paid ads"],
        "approved": False,
    }