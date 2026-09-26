from state import StartupState
from tools.risk_tools import check_financial_risks, check_manual_constraints


def risk_reviewer(state: StartupState) -> dict:
    risks = check_financial_risks.invoke({
        "values": {
            "expected_profit": state.expected_profit,
            "break_even_sales": state.break_even_sales,
            "proposed_sales": state.proposed_sales,
            "proposed_price": state.proposed_price,
            "cost_per_sale": state.cost_per_sale,
            "max_price": state.max_price,
        },
    })
    risks.extend(check_manual_constraints.invoke({
        "constraints": state.constraints,
    }))

    return {
        "risks": risks,
        "approved": len(risks) == 0,
    }
