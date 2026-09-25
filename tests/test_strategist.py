from unittest.mock import patch

import pytest

from agents.strategist import launch_strategist
from models.schemas import LaunchStrategyOutput
from state import StartupState


@pytest.mark.parametrize("revision_count", [0, 1])
def test_launch_strategist_prompt_includes_price_cap(revision_count):
    cap_risk = (
        "Proposed price 8.0 exceeds max_price 7.0. "
        "Lower the proposed price to 7.0 or less."
    )
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        max_price=7,
        revision_count=revision_count,
    )
    if revision_count > 0:
        state = state.model_copy(update={
            "risks": [cap_risk],
            "target_customer": "University students",
            "launch_strategy": "Promote through campus clubs.",
            "proposed_price": 8.0,
            "proposed_sales": 100,
        })
    original_state = state.model_dump()
    output = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Promote through campus clubs and Instagram.",
        proposed_price=7,
        proposed_sales=100,
    )

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = mock_model.return_value.with_structured_output.return_value
        structured_model.invoke.return_value = output

        result = launch_strategist(state)

        structured_model.invoke.assert_called_once()
        prompt = structured_model.invoke.call_args.args[0]
        assert "Maximum allowed price (max_price): 7.0" in prompt
        assert "cost_per_sale < proposed_price <= max_price" in prompt
        if revision_count > 0:
            assert cap_risk in prompt
            assert "Improve the previous proposal" in prompt

    assert result == output.model_dump()
    assert state.model_dump() == original_state


def test_launch_strategist_initial_pass():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        revision_count=0,
    )
    original_state = state.model_dump()
    output = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Promote through campus clubs and Instagram.",
        proposed_price=8.0,
        proposed_sales=100,
    )

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = mock_model.return_value.with_structured_output.return_value
        structured_model.invoke.return_value = output

        result = launch_strategist(state)

        mock_model.assert_called_once_with(model="gpt-5-mini", temperature=0)
        mock_model.return_value.with_structured_output.assert_called_once_with(
            LaunchStrategyOutput
        )
        structured_model.invoke.assert_called_once()
        prompt = structured_model.invoke.call_args.args[0]
        assert "Create a realistic startup launch plan." in prompt

    assert result == {
        "target_customer": "University students",
        "launch_strategy": "Promote through campus clubs and Instagram.",
        "proposed_price": 8.0,
        "proposed_sales": 100,
    }
    assert state.model_dump() == original_state


def test_launch_strategist_revision_includes_risks_and_previous_proposal():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        revision_count=1,
        risks=["Advertising is too expensive", "Sales estimate is too optimistic"],
        target_customer="Local office workers",
        launch_strategy="Use paid billboard advertising.",
        proposed_price=7.0,
        proposed_sales=200,
    )
    original_state = state.model_dump()
    output = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Promote through campus clubs and Instagram.",
        proposed_price=8.0,
        proposed_sales=100,
    )

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = mock_model.return_value.with_structured_output.return_value
        structured_model.invoke.return_value = output

        result = launch_strategist(state)

        structured_model.invoke.assert_called_once()
        prompt = structured_model.invoke.call_args.args[0]
        assert "Improve the previous proposal based on the reviewer risks." in prompt
        assert "Revision count: 1" in prompt
        for risk in state.risks:
            assert risk in prompt
        assert "Target customer: Local office workers" in prompt
        assert "Launch strategy: Use paid billboard advertising." in prompt
        assert "Proposed price: 7.0" in prompt
        assert "Proposed sales: 200" in prompt

    assert result == output.model_dump()
    assert state.model_dump() == original_state


@pytest.mark.parametrize("proposed_price", [4.0, 3.0])
def test_launch_strategist_rejects_price_at_or_below_cost(proposed_price):
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
    )
    original_state = state.model_dump()
    output = LaunchStrategyOutput(
        target_customer="University students",
        launch_strategy="Promote through campus clubs and Instagram.",
        proposed_price=proposed_price,
        proposed_sales=100,
    )

    with patch("agents.strategist.ChatOpenAI") as mock_model:
        structured_model = mock_model.return_value.with_structured_output.return_value
        structured_model.invoke.return_value = output

        with pytest.raises(
            ValueError, match="Proposed price must be greater than cost per sale"
        ):
            launch_strategist(state)

    assert state.model_dump() == original_state
