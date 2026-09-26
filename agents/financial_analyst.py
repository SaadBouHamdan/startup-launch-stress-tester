from state import StartupState
from tools.financial_tools import (
    calculate_break_even_tool,
    calculate_profit_tool,
)


def financial_analyst(state: StartupState) -> dict[str, int | float | None]:
    selling_price = (
        state.proposed_price
        if state.proposed_price is not None
        else state.selling_price
    )
    expected_sales = (
        state.proposed_sales
        if state.proposed_sales is not None
        else state.expected_sales
    )

    # Add the Strategist's new expenses to the original costs.
    fixed_costs = state.monthly_fixed_costs + sum(
        cost.monthly_fixed for cost in state.added_costs
    )
    cost_per_sale = state.cost_per_sale + sum(
        cost.per_sale for cost in state.added_costs
    )

    # If each sale costs as much as (or more than) its selling price,
    # break-even cannot be reached. Leave it as None so the Reviewer
    # can reject the plan instead of stopping the graph with an error.
    if selling_price > cost_per_sale:
        break_even_sales = calculate_break_even_tool.invoke({
            "selling_price": selling_price,
            "cost_per_sale": cost_per_sale,
            "fixed_costs": fixed_costs,
        })
    else:
        break_even_sales = None

    expected_profit = calculate_profit_tool.invoke({
        "selling_price": selling_price,
        "cost_per_sale": cost_per_sale,
        "fixed_costs": fixed_costs,
        "expected_sales": expected_sales,
    })

    return {
        "break_even_sales": break_even_sales,
        "expected_profit": expected_profit,
        "total_monthly_fixed_costs": fixed_costs,
        "total_cost_per_sale": cost_per_sale,
    }