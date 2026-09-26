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

Respect the constraints and propose practical actions for this specific business.
Do not increase expected sales just to make a plan appear profitable.
Proposed sales must be a realistic estimate for one month.
The proposed price must be greater than the original cost per sale.

The supplied cost_per_sale and monthly_fixed_costs are the totals for the
existing business before your new launch actions. Their itemized breakdown
was not supplied. Do not invent a breakdown or list questions about that
breakdown in unpriced_paid_actions.

Cost rules:
- List every paid action included in your proposed month-one plan in
  added_costs. List only costs added by that action beyond the supplied
  starting costs.
- Record each expense once. A capped monthly budget, such as $50 for ads,
  belongs in monthly_fixed with per_sale set to 0. Do not also divide that
  same budget by expected sales and enter it in per_sale.
- Each AddedCost entry must have a positive amount in only one cost field:
  monthly_fixed OR per_sale. If a service has a separate subscription and
  a separate transaction fee, use two entries with clear descriptions.
- per_sale means the average additional cost across ALL projected sales.
  For a cost that applies only to some orders, multiply its cost by the
  expected share of orders. For example, a $2 commission on an estimated
  30% of sales is $0.60 per sale on average. Explain that estimate.
- Do not add ordinary existing costs again merely because the supplied
  totals have no breakdown. Include processing, packaging, or delivery
  costs only if your proposed action introduces an additional expense.
- Include optional or conditional actions in added_costs if they are part
  of the month-one plan. Their budget will be counted in the financial
  calculation. Do not claim that an included cost is excluded.
- unpriced_paid_actions is only for paid actions included in this month-one
  plan whose additional cost you cannot estimate. Do not put future
  alternatives or questions about the original inputs in that list.
- Clearly label any future alternative as outside the proposed month-one
  plan. Do not include its costs or describe it as an action to carry out
  during month one.
- For a discount, make proposed_price reflect the effective price per
  sale, or omit the discount.
- If production requires a minimum number of preorders, make that
  threshold consistent with proposed monthly sales.
- Do not calculate break-even or profit in your strategy. The Financial
  Analyst calculates those values.

Startup idea: {state.startup_idea}
Original selling price: {state.selling_price}
Original cost per sale: {state.cost_per_sale}
Original monthly fixed costs: {state.monthly_fixed_costs}
Original expected monthly sales: {state.expected_sales}
Constraints: {state.constraints}
Revision count: {state.revision_count}
Previous reviewer risks: {state.risks}

Previous proposal (None means not available):
Target customer: {state.target_customer}
Launch strategy: {state.launch_strategy}
Proposed price: {state.proposed_price}
Proposed sales: {state.proposed_sales}
Previously added costs: {state.added_costs}
Previously unpriced paid actions: {state.unpriced_paid_actions}
"""

    if state.max_price is not None:
        prompt += (
            f"\nMaximum allowed price (max_price): {state.max_price}\n"
            "The proposal must satisfy: "
            "cost_per_sale < proposed_price <= max_price.\n"
        )

    result = structured_model.invoke(prompt)

    if result.proposed_price <= state.cost_per_sale:
        raise ValueError("Proposed price must be greater than cost per sale.")

    return {
        "target_customer": result.target_customer,
        "launch_strategy": result.launch_strategy,
        "proposed_price": result.proposed_price,
        "proposed_sales": result.proposed_sales,
        "added_costs": [
            cost.model_dump() for cost in result.added_costs
        ],
        "unpriced_paid_actions": result.unpriced_paid_actions,
    }