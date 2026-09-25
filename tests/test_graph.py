from unittest.mock import patch
from uuid import uuid4

import pytest

from graph import graph, increment_revision, route_after_review
from models.schemas import LaunchStrategyOutput
from state import StartupState


def test_graph_revises_price_above_cap_and_approves():
    state = StartupState(
        startup_idea="Custom university T-shirt business",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        constraints=[],
        max_price=7,
    )
    original_state = state.model_dump()
    first_proposal = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Promote through campus clubs.",
        proposed_price=8,
        proposed_sales=100,
    )
    revised_proposal = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Offer affordable T-shirts through campus clubs.",
        proposed_price=7,
        proposed_sales=100,
    )
    config = {"configurable": {"thread_id": str(uuid4())}}

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = mock_model.return_value.with_structured_output.return_value
        structured_model.invoke.side_effect = [first_proposal, revised_proposal]

        updates = list(graph.stream(state.model_dump(), config, stream_mode="updates"))

        assert structured_model.invoke.call_count == 2
        revision_prompt = structured_model.invoke.call_args_list[1].args[0]

    cap_risk = (
        "Proposed price 8.0 exceeds max_price 7.0. "
        "Lower the proposed price to 7.0 or less."
    )
    assert [next(iter(update)) for update in updates] == [
        "strategist", "financial_analyst", "risk_reviewer", "revise",
        "strategist", "financial_analyst", "risk_reviewer",
    ]
    assert updates[0]["strategist"] == first_proposal.model_dump()
    assert updates[1]["financial_analyst"] == {
        "break_even_sales": 75, "expected_profit": 100,
    }
    assert updates[2]["risk_reviewer"] == {"risks": [cap_risk], "approved": False}
    assert updates[3]["revise"] == {"revision_count": 1}
    assert updates[4]["strategist"] == revised_proposal.model_dump()
    assert updates[5]["financial_analyst"] == {
        "break_even_sales": 100, "expected_profit": 0,
    }
    assert updates[6]["risk_reviewer"] == {"risks": [], "approved": True}
    assert cap_risk in revision_prompt
    assert "Maximum allowed price (max_price): 7.0" in revision_prompt
    assert "Revision count: 1" in revision_prompt

    final_state = graph.get_state(config).values
    assert final_state["approved"] is True
    assert final_state["revision_count"] == 1
    assert final_state["proposed_price"] == 7
    assert final_state["proposed_sales"] == 100
    assert final_state["break_even_sales"] == 100
    assert final_state["expected_profit"] == 0
    assert final_state["risks"] == []
    assert final_state["max_price"] == 7
    assert state.model_dump() == original_state


@pytest.mark.parametrize(
    "approved, revision_count, max_revisions, expected_route",
    [
        (True, 0, 3, "end"),
        (False, 1, 3, "revise"),
        (False, 3, 3, "end"),
    ],
)
def test_route_after_review(approved, revision_count, max_revisions, expected_route):
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        approved=approved,
        revision_count=revision_count,
        max_revisions=max_revisions,
    )

    assert route_after_review(state) == expected_route


def test_increment_revision_does_not_mutate_state():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        revision_count=1,
    )
    original_state = state.model_dump()

    result = increment_revision(state)

    assert result == {"revision_count": 2}
    assert state.model_dump() == original_state
