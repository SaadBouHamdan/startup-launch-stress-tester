import math

from state import StartupState


def risk_reviewer(state: StartupState) -> dict:
    risks = []
    numeric_fields = {
        "expected_profit": state.expected_profit,
        "break_even_sales": state.break_even_sales,
        "proposed_sales": state.proposed_sales,
        "proposed_price": state.proposed_price,
        "cost_per_sale": state.cost_per_sale,
    }
    if state.max_price is not None:
        numeric_fields["max_price"] = state.max_price
    valid_values = {}

    for name, value in numeric_fields.items():
        if value is None:
            risks.append(f"Missing required field: {name}.")
        elif isinstance(value, bool) or not isinstance(value, (int, float)):
            risks.append(f"{name} must be a valid finite number.")
        elif isinstance(value, float) and not math.isfinite(value):
            risks.append(f"{name} must be a valid finite number.")
        else:
            valid_values[name] = value

    for name in ("cost_per_sale", "proposed_sales", "break_even_sales"):
        if name in valid_values and valid_values[name] < 0:
            risks.append(f"{name} must not be negative.")

    if "proposed_price" in valid_values:
        if valid_values["proposed_price"] <= 0:
            risks.append("Proposed price must be greater than zero.")
        if (
            "cost_per_sale" in valid_values
            and valid_values["proposed_price"] <= valid_values["cost_per_sale"]
        ):
            risks.append("Proposed price must be greater than cost per sale.")

    if (
        "proposed_price" in valid_values
        and "max_price" in valid_values
        and valid_values["proposed_price"] > valid_values["max_price"]
    ):
        risks.append(
            f"Proposed price {state.proposed_price} exceeds max_price {state.max_price}. "
            f"Lower the proposed price to {state.max_price} or less."
        )

    if "expected_profit" in valid_values and valid_values["expected_profit"] < 0:
        risks.append("Expected profit is negative.")

    if (
        "proposed_sales" in valid_values
        and "break_even_sales" in valid_values
        and valid_values["proposed_sales"] < valid_values["break_even_sales"]
    ):
        risks.append("Proposed sales are below break-even sales.")

    for constraint in state.constraints:
        if constraint.strip():
            risks.append(f"Constraint requires manual verification: {constraint}")

    return {
        "risks": risks,
        "approved": len(risks) == 0,
    }
