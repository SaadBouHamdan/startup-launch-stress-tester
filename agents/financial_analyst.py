from state import StartupState
from tools.financial_tools import calculate_break_even, calculate_profit


def financial_analyst(state: StartupState) -> dict[str, int | float]:
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

    break_even_sales = calculate_break_even(
        selling_price,
        state.cost_per_sale,
        state.monthly_fixed_costs,
    )
    expected_profit = calculate_profit(
        selling_price,
        state.cost_per_sale,
        state.monthly_fixed_costs,
        expected_sales,
    )

    return {
        "break_even_sales": break_even_sales,
        "expected_profit": expected_profit,
    }
