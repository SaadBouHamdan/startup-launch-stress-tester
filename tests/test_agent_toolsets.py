from unittest.mock import patch

import pytest
from langchain_core.tools import BaseTool

from agents.financial_analyst import financial_analyst
from agents.risk_reviewer import risk_reviewer
from state import StartupState
from tools.financial_tools import calculate_break_even_tool, calculate_profit_tool
from tools.risk_tools import check_financial_risks, check_manual_constraints


@pytest.mark.parametrize("fixed_costs, expected", [(300, 150), (301, 151)])
def test_break_even_tool(fixed_costs, expected):
    assert calculate_break_even_tool.invoke({
        "selling_price": 6,
        "cost_per_sale": 4,
        "fixed_costs": fixed_costs,
    }) == expected


@pytest.mark.parametrize("selling_price", [4, 3])
def test_break_even_tool_preserves_margin_error(selling_price):
    with pytest.raises(ValueError, match="Selling price must be greater than cost per sale"):
        calculate_break_even_tool.invoke({
            "selling_price": selling_price,
            "cost_per_sale": 4,
            "fixed_costs": 300,
        })


def test_profit_tool():
    assert calculate_profit_tool.invoke({
        "selling_price": 6,
        "cost_per_sale": 4,
        "fixed_costs": 300,
        "expected_sales": 80,
    }) == -140


@pytest.fixture
def financial_values():
    return {
        "expected_profit": 100.0,
        "break_even_sales": 75.0,
        "proposed_sales": 100,
        "proposed_price": 8.0,
        "cost_per_sale": 4.0,
        "max_price": None,
    }


@pytest.mark.parametrize("max_price", [None, 8.0, 9.0])
def test_financial_risk_tool_accepts_valid_values(financial_values, max_price):
    financial_values["max_price"] = max_price
    original_values = financial_values.copy()

    assert check_financial_risks.invoke({"values": financial_values}) == []
    assert financial_values == original_values


def test_financial_risk_tool_preserves_message_order(financial_values):
    financial_values.update({
        "max_price": 7.0,
        "expected_profit": -140.0,
        "proposed_sales": 80,
        "break_even_sales": 150.0,
    })

    assert check_financial_risks.invoke({"values": financial_values}) == [
        "Proposed price 8.0 exceeds max_price 7.0. Lower the proposed price to 7.0 or less.",
        "Expected profit is negative.",
        "Proposed sales are below break-even sales.",
    ]


def test_financial_risk_tool_reports_missing_values():
    assert check_financial_risks.invoke({"values": {"cost_per_sale": 4}}) == [
        "Missing required field: expected_profit.",
        "Missing required field: break_even_sales.",
        "Missing required field: proposed_sales.",
        "Missing required field: proposed_price.",
    ]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), "invalid", True])
def test_financial_risk_tool_reports_invalid_values(financial_values, value):
    financial_values["max_price"] = value

    assert check_financial_risks.invoke({"values": financial_values}) == [
        "max_price must be a valid finite number.",
    ]


def test_financial_risk_tool_preserves_negative_value_checks(financial_values):
    financial_values.update({
        "cost_per_sale": -1,
        "proposed_sales": -2,
        "break_even_sales": -1,
        "proposed_price": -2,
    })

    assert check_financial_risks.invoke({"values": financial_values}) == [
        "cost_per_sale must not be negative.",
        "proposed_sales must not be negative.",
        "break_even_sales must not be negative.",
        "Proposed price must be greater than zero.",
        "Proposed price must be greater than cost per sale.",
        "Proposed sales are below break-even sales.",
    ]


def test_manual_constraint_tool_preserves_messages_and_input():
    constraints = ["", "  ", "Do not sell on campus", "Use local suppliers"]
    original_constraints = constraints.copy()

    assert check_manual_constraints.invoke({"constraints": constraints}) == [
        "Constraint requires manual verification: Do not sell on campus",
        "Constraint requires manual verification: Use local suppliers",
    ]
    assert constraints == original_constraints


def test_manual_constraint_tool_accepts_empty_constraints():
    assert check_manual_constraints.invoke({"constraints": []}) == []


@pytest.mark.parametrize("proposed_price, proposed_sales", [(None, None), (8, 100)])
def test_agents_invoke_distinct_assigned_toolsets(proposed_price, proposed_sales):
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=proposed_price,
        proposed_sales=proposed_sales,
        max_price=7,
        constraints=["Do not sell on campus"],
    )
    original_state = state.model_dump()
    calls = []
    original_invoke = BaseTool.invoke

    def record_invoke(tool, inputs, *args, **kwargs):
        calls.append((tool.name, inputs))
        return original_invoke(tool, inputs, *args, **kwargs)

    # Record actual tool invocations while still executing deterministic tools.
    with patch.object(BaseTool, "invoke", autospec=True, side_effect=record_invoke):
        financial_result = financial_analyst(state)
        financial_calls = calls.copy()
        calls.clear()
        reviewed_state = state.model_copy(update=financial_result)
        result = risk_reviewer(reviewed_state)
        risk_calls = calls.copy()

    price = 6 if proposed_price is None else proposed_price
    sales = 80 if proposed_sales is None else proposed_sales
    assert financial_calls == [
        ("calculate_break_even_tool", {
            "selling_price": price, "cost_per_sale": 4, "fixed_costs": 300,
        }),
        ("calculate_profit_tool", {
            "selling_price": price, "cost_per_sale": 4,
            "fixed_costs": 300, "expected_sales": sales,
        }),
    ]
    assert risk_calls == [
        ("check_financial_risks", {"values": {
            "expected_profit": financial_result["expected_profit"],
            "break_even_sales": financial_result["break_even_sales"],
            "proposed_sales": proposed_sales,
            "proposed_price": proposed_price,
            "cost_per_sale": 4,
            "max_price": 7,
        }}),
        ("check_manual_constraints", {"constraints": ["Do not sell on campus"]}),
    ]
    financial_toolset = {name for name, inputs in financial_calls}
    risk_toolset = {name for name, inputs in risk_calls}
    assert financial_toolset != risk_toolset
    assert financial_toolset.isdisjoint(risk_toolset)
    assert result["approved"] is False
    assert result["risks"][-1] == "Constraint requires manual verification: Do not sell on campus"
    assert state.model_dump() == original_state
    assert reviewed_state.model_dump() == {**original_state, **financial_result}
