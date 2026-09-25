from agents.financial_analyst import financial_analyst
from state import StartupState


def test_financial_analyst_uses_original_values():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
    )

    result = financial_analyst(state)

    assert result == {
        "break_even_sales": 150,
        "expected_profit": -140,
    }


def test_financial_analyst_uses_proposed_values():
    state = StartupState(
        startup_idea="Coffee stand",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=8,
        proposed_sales=100,
    )

    result = financial_analyst(state)

    assert result == {
        "break_even_sales": 75,
        "expected_profit": 100,
    }
