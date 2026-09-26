from unittest.mock import patch

import pytest

from web_server import analyze, validate_inputs


VALID = {
    "startup_idea": "Campus coffee delivery",
    "selling_price": 6,
    "cost_per_sale": 2,
    "monthly_fixed_costs": 120,
    "expected_sales": 80,
    "max_price": None,
    "constraints": ["No paid ads"],
}


def test_guided_answers_become_graph_state():
    state = validate_inputs(VALID)

    assert state.startup_idea == "Campus coffee delivery"
    assert state.expected_sales == 80
    assert state.constraints == ["No paid ads"]
    assert state.max_price is None


@pytest.mark.parametrize(
    "change",
    [
        {"selling_price": 0},
        {"cost_per_sale": -1},
        {"monthly_fixed_costs": float("nan")},
        {"expected_sales": 1.5},
        {"max_price": 0},
        {"constraints": "No paid ads"},
    ],
)
def test_invalid_answers_are_rejected_before_model_call(change):
    with pytest.raises(ValueError):
        validate_inputs({**VALID, **change})


def test_analysis_uses_graph_and_returns_review_fields():
    final = {
        "startup_idea": "Campus coffee delivery",
        "target_customer": "Students",
        "launch_strategy": "Take prepaid orders.",
        "proposed_price": 6,
        "proposed_sales": 80,
        "added_costs": [],
        "total_monthly_fixed_costs": 120,
        "total_cost_per_sale": 2,
        "break_even_sales": 30,
        "expected_profit": 200,
        "risks": [],
        "approved": True,
        "revision_count": 0,
        "unpriced_paid_actions": [],
    }
    with patch("web_server.graph.invoke", return_value=final) as invoke:
        result = analyze(VALID)

    assert invoke.call_args.args[0]["startup_idea"] == VALID["startup_idea"]
    assert invoke.call_args.kwargs["config"]["configurable"]["thread_id"]
    assert result["expected_profit"] == 200
    assert result["approved"] is True
