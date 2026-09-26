import math

from langchain_core.tools import tool


def calculate_break_even(
    selling_price: float,
    cost_per_sale: float,
    fixed_costs: float
) -> int:
    contribution_margin = selling_price - cost_per_sale

    if contribution_margin <= 0:
        raise ValueError("Selling price must be greater than cost per sale.")

    return math.ceil(fixed_costs / contribution_margin)


def calculate_profit(
    selling_price: float,
    cost_per_sale: float,
    fixed_costs: float,
    expected_sales: int
) -> float:
    return (selling_price - cost_per_sale) * expected_sales - fixed_costs


@tool
def calculate_break_even_tool(
    selling_price: float,
    cost_per_sale: float,
    fixed_costs: float,
) -> int:
    """Calculate the number of sales needed to cover fixed costs."""
    return calculate_break_even(selling_price, cost_per_sale, fixed_costs)


@tool
def calculate_profit_tool(
    selling_price: float,
    cost_per_sale: float,
    fixed_costs: float,
    expected_sales: int,
) -> float:
    """Calculate expected profit from price, costs, and expected sales."""
    return calculate_profit(
        selling_price, cost_per_sale, fixed_costs, expected_sales
    )
