from unittest.mock import patch
from uuid import uuid4

import pytest

from graph import graph, increment_revision, route_after_review
from models.schemas import AddedCost, LaunchStrategyOutput
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
        structured_model = (
            mock_model.return_value.with_structured_output.return_value
        )
        structured_model.invoke.side_effect = [
            first_proposal,
            revised_proposal,
        ]

        updates = list(
            graph.stream(
                state.model_dump(),
                config,
                stream_mode="updates",
            )
        )

        assert structured_model.invoke.call_count == 2
        revision_prompt = structured_model.invoke.call_args_list[1].args[0]

    cap_risk = (
        "Proposed price 8.0 exceeds max_price 7.0. "
        "Lower the proposed price to 7.0 or less."
    )

    assert [next(iter(update)) for update in updates] == [
        "strategist",
        "financial_analyst",
        "risk_reviewer",
        "revise",
        "strategist",
        "financial_analyst",
        "risk_reviewer",
    ]
    assert updates[0]["strategist"] == first_proposal.model_dump()
    assert updates[1]["financial_analyst"] == {
        "break_even_sales": 75,
        "expected_profit": 100,
        "total_monthly_fixed_costs": 300,
        "total_cost_per_sale": 4,
    }
    assert updates[2]["risk_reviewer"] == {
        "risks": [cap_risk],
        "warnings": [],
        "approved": False,
    }
    assert updates[3]["revise"] == {"revision_count": 1}
    assert updates[4]["strategist"] == revised_proposal.model_dump()
    assert updates[5]["financial_analyst"] == {
        "break_even_sales": 100,
        "expected_profit": 0,
        "total_monthly_fixed_costs": 300,
        "total_cost_per_sale": 4,
    }
    assert updates[6]["risk_reviewer"] == {
        "risks": [],
        "warnings": [],
        "approved": True,
    }
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


def test_graph_stops_after_all_revisions_are_rejected():
    state = StartupState(
        startup_idea="Custom university T-shirt business",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        max_price=7,
        max_revisions=3,
    )
    rejected_proposal = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Promote through campus clubs.",
        proposed_price=8,
        proposed_sales=100,
    )
    config = {
        "configurable": {"thread_id": str(uuid4())},
        "recursion_limit": 25,
    }

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = (
            mock_model.return_value.with_structured_output.return_value
        )
        structured_model.invoke.return_value = rejected_proposal

        updates = list(
            graph.stream(
                state.model_dump(),
                config,
                stream_mode="updates",
            )
        )

        assert structured_model.invoke.call_count == 4
        for revision, call in enumerate(
            structured_model.invoke.call_args_list
        ):
            assert f"Revision count: {revision}" in call.args[0]

    assert [next(iter(update)) for update in updates] == [
        "strategist",
        "financial_analyst",
        "risk_reviewer",
        "revise",
        "strategist",
        "financial_analyst",
        "risk_reviewer",
        "revise",
        "strategist",
        "financial_analyst",
        "risk_reviewer",
        "revise",
        "strategist",
        "financial_analyst",
        "risk_reviewer",
    ]

    revision_updates = [
        update["revise"]["revision_count"]
        for update in updates
        if "revise" in update
    ]
    assert revision_updates == [1, 2, 3]

    reviews = [
        update["risk_reviewer"]
        for update in updates
        if "risk_reviewer" in update
    ]
    assert len(reviews) == 4

    for review in reviews:
        assert review["approved"] is False
        assert review["risks"] == [
            "Proposed price 8.0 exceeds max_price 7.0. "
            "Lower the proposed price to 7.0 or less."
        ]

    final_snapshot = graph.get_state(config)
    assert final_snapshot.values["approved"] is False
    assert final_snapshot.values["revision_count"] == 3
    assert final_snapshot.values["risks"]
    assert final_snapshot.next == ()


@pytest.mark.parametrize(
    "approved, revision_count, max_revisions, expected_route",
    [
        (True, 0, 3, "end"),
        (False, 1, 3, "revise"),
        (False, 3, 3, "end"),
    ],
)
def test_route_after_review(
    approved,
    revision_count,
    max_revisions,
    expected_route,
):
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


def test_graph_revises_after_unpriced_expense_and_recalculates():
    state = StartupState(
        startup_idea="Printed mugs",
        selling_price=12,
        cost_per_sale=5,
        monthly_fixed_costs=300,
        expected_sales=80,
        max_revisions=1,
    )
    first_proposal = LaunchStrategyOutput(
        target_customer="Students",
        launch_strategy="Buy paid ads.",
        proposed_price=12,
        proposed_sales=80,
        unpriced_paid_actions=["Paid ads"],
    )
    revised_proposal = LaunchStrategyOutput(
        target_customer="Students",
        launch_strategy="Budget ads, shop, and packaging.",
        proposed_price=12,
        proposed_sales=80,
        added_costs=[
            AddedCost(description="Ads", monthly_fixed=100),
            AddedCost(description="Online shop", monthly_fixed=40),
            AddedCost(description="Packaging", per_sale=1),
        ],
    )
    config = {"configurable": {"thread_id": str(uuid4())}}

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = (
            mock_model.return_value.with_structured_output.return_value
        )
        structured_model.invoke.side_effect = [
            first_proposal,
            revised_proposal,
        ]

        updates = list(
            graph.stream(
                state.model_dump(),
                config,
                stream_mode="updates",
            )
        )

    assert updates[2]["risk_reviewer"]["approved"] is False
    assert updates[2]["risk_reviewer"]["risks"] == [
        "Paid action needs a cost estimate: Paid ads"
    ]
    assert updates[5]["financial_analyst"]["expected_profit"] == 40
    assert updates[5]["financial_analyst"]["break_even_sales"] == 74
    assert graph.get_state(config).values["approved"] is True

def test_graph_approves_profitable_plan_with_constraint_on_first_attempt():
    state = StartupState(
        startup_idea="Custom university T-shirt business",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        max_price=7,
        constraints=["No paid ads"],
    )
    proposal = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Sell through campus clubs without paid ads.",
        proposed_price=7,
        proposed_sales=120,
    )
    config = {"configurable": {"thread_id": str(uuid4())}}

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = (
            mock_model.return_value.with_structured_output.return_value
        )
        structured_model.invoke.return_value = proposal

        result = graph.invoke(state.model_dump(), config)

        assert structured_model.invoke.call_count == 1

    assert result["approved"] is True
    assert result["revision_count"] == 0
    assert result["risks"] == []
    assert result["warnings"] == [
        "Constraint requires manual verification: No paid ads"
    ]