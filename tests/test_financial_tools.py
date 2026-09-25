import pytest

from tools.financial_tools import calculate_break_even, calculate_profit


def test_financial_helpers():
    selling_price = 6
    cost_per_sale = 4
    fixed_costs = 300
    expected_sales = 80

    assert calculate_break_even(selling_price, cost_per_sale, fixed_costs) == 150
    assert calculate_profit(
        selling_price, cost_per_sale, fixed_costs, expected_sales
    ) == -140


def test_break_even_raises_when_price_equals_cost():
    with pytest.raises(ValueError):
        calculate_break_even(4, 4, 300)


def test_break_even_raises_when_price_is_below_cost():
    with pytest.raises(ValueError):
        calculate_break_even(3, 4, 300)
