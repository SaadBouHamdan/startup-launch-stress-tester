from langchain_openai import ChatOpenAI

from models.schemas import LaunchStrategyOutput
from state import StartupState


def launch_strategist(state: StartupState) -> dict:
    model = ChatOpenAI(model="gpt-5-mini", temperature=0)
    structured_model = model.with_structured_output(LaunchStrategyOutput)

    if state.revision_count == 0:
        task = "Create a realistic startup launch plan."
    else:
        task = "Improve the previous proposal based on the reviewer risks."

    prompt = f"""
You are the Launch Strategist for a startup.
{task}
Respect the constraints and explain a practical approach in the launch strategy.
Do not inflate sales unrealistically just to make the plan profitable.
Proposed sales must represent realistic expected sales for one month.
The proposed_price must be greater than cost_per_sale.

Startup idea: {state.startup_idea}
Original selling price: {state.selling_price}
Cost per sale: {state.cost_per_sale}
Monthly fixed costs: {state.monthly_fixed_costs}
Original expected sales: {state.expected_sales}
Constraints: {state.constraints}
Revision count: {state.revision_count}
Previous reviewer risks: {state.risks}

Previous proposal (None means not available):
Target customer: {state.target_customer}
Launch strategy: {state.launch_strategy}
Proposed price: {state.proposed_price}
Proposed sales: {state.proposed_sales}
"""

    if state.max_price is not None:
        prompt += (
            f"\nMaximum allowed price (max_price): {state.max_price}\n"
            "The proposal must satisfy: cost_per_sale < proposed_price <= max_price.\n"
        )

    result = structured_model.invoke(prompt)

    if result.proposed_price <= state.cost_per_sale:
        raise ValueError("Proposed price must be greater than cost per sale.")

    return {
        "target_customer": result.target_customer,
        "launch_strategy": result.launch_strategy,
        "proposed_price": result.proposed_price,
        "proposed_sales": result.proposed_sales,
    }
