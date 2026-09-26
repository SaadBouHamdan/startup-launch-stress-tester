from agents.financial_analyst import financial_analyst
from models.schemas import AddedCost
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
        "total_monthly_fixed_costs": 300,
        "total_cost_per_sale": 4,
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
        "total_monthly_fixed_costs": 300,
        "total_cost_per_sale": 4,
    }


def test_added_monthly_and_per_sale_costs_change_profit_and_break_even():
    state = StartupState(
        startup_idea="Printed mugs",
        selling_price=12,
        cost_per_sale=5,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=12,
        proposed_sales=80,
        added_costs=[
            AddedCost(description="Ads", monthly_fixed=100),
            AddedCost(description="Online shop", monthly_fixed=40),
            AddedCost(description="Packaging", per_sale=1),
        ],
    )

    result = financial_analyst(state)

    assert result == {
        "break_even_sales": 74,
        "expected_profit": 40,
        "total_monthly_fixed_costs": 440,
        "total_cost_per_sale": 6,
    }


def test_added_per_sale_cost_can_eliminate_margin_without_crashing():
    state = StartupState(
        startup_idea="Printed mugs",
        selling_price=7,
        cost_per_sale=5,
        monthly_fixed_costs=300,
        expected_sales=80,
        proposed_price=7,
        proposed_sales=80,
        added_costs=[
            AddedCost(description="Referral bonus", per_sale=3),
        ],
    )

    result = financial_analyst(state)

    assert result["break_even_sales"] is None
    assert result["expected_profit"] == -380