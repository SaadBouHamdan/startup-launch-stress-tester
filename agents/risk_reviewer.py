from state import StartupState
from tools.risk_tools import check_financial_risks, check_manual_constraints


def risk_reviewer(state: StartupState) -> dict:
    risks = check_financial_risks.invoke({
        "values": {
            "expected_profit": state.expected_profit,
            "break_even_sales": state.break_even_sales,
            "proposed_sales": state.proposed_sales,
            "proposed_price": state.proposed_price,
            "cost_per_sale": (
                state.total_cost_per_sale
                if state.total_cost_per_sale is not None
                else state.cost_per_sale
            ),
            "max_price": state.max_price,
        },
    })

    # Free-text constraints cannot be verified automatically. Report them
    # as warnings for a person to check; they do not block approval.
    warnings = check_manual_constraints.invoke({
        "constraints": state.constraints,
    })

    for cost in state.added_costs:
        if cost.monthly_fixed > 0 and cost.per_sale > 0:
            risks.append(
                "Cost entered as both monthly and per-sale: "
                f"{cost.description}. Count the expense once; "
                "use separate entries for genuinely separate charges."
            )

    risks.extend(
        f"Paid action needs a cost estimate: {action}"
        for action in state.unpriced_paid_actions
        if action.strip()
    )

    return {
        "risks": risks,
        "warnings": warnings,
        "approved": len(risks) == 0,
    }