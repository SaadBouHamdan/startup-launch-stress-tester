import math
from typing import Any

from langchain_core.tools import tool


@tool
def check_financial_risks(values: dict[str, Any]) -> list[str]:
    """Check financial values and the optional price cap, returning risk messages."""
    risks = []
    numeric_fields = {
        "expected_profit": values.get("expected_profit"),
        "break_even_sales": values.get("break_even_sales"),
        "proposed_sales": values.get("proposed_sales"),
        "proposed_price": values.get("proposed_price"),
        "cost_per_sale": values.get("cost_per_sale"),
    }
    if values.get("max_price") is not None:
        numeric_fields["max_price"] = values.get("max_price")
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
            f"Proposed price {values.get('proposed_price')} exceeds max_price {values.get('max_price')}. "
            f"Lower the proposed price to {values.get('max_price')} or less."
        )

    if "expected_profit" in valid_values and valid_values["expected_profit"] < 0:
        risks.append("Expected profit is negative.")

    if (
        "proposed_sales" in valid_values
        and "break_even_sales" in valid_values
        and valid_values["proposed_sales"] < valid_values["break_even_sales"]
    ):
        risks.append("Proposed sales are below break-even sales.")

    return risks


@tool
def check_manual_constraints(constraints: list[str]) -> list[str]:
    """Flag each nonblank constraint as requiring manual verification."""
    risks = []
    for constraint in constraints:
        if constraint.strip():
            risks.append(f"Constraint requires manual verification: {constraint}")

    return risks
