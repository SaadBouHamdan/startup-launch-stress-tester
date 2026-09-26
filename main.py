import argparse
import sys
from uuid import uuid4

from dotenv import load_dotenv

from graph import graph
from state import StartupState


def get_initial_state() -> StartupState:
    parser = argparse.ArgumentParser(
        description="Evaluate a startup launch plan."
    )
    parser.add_argument("--idea", help="Startup idea to evaluate")
    parser.add_argument("--selling-price", type=float)
    parser.add_argument("--cost-per-sale", type=float)
    parser.add_argument("--monthly-fixed-costs", type=float)
    parser.add_argument("--expected-sales", type=int)
    parser.add_argument("--max-price", type=float)
    parser.add_argument("--max-revisions", type=int, default=3)
    parser.add_argument(
        "--constraint",
        action="append",
        default=[],
        help="Add a constraint; this option can be used more than once.",
    )
    args = parser.parse_args()

    if args.max_revisions < 0:
        parser.error("--max-revisions cannot be negative.")

    financial_inputs = {
        "--selling-price": args.selling_price,
        "--cost-per-sale": args.cost_per_sale,
        "--monthly-fixed-costs": args.monthly_fixed_costs,
        "--expected-sales": args.expected_sales,
    }

    if args.idea is None:
        if any(value is not None for value in financial_inputs.values()):
            parser.error(
                "When providing custom financial inputs, also provide --idea."
            )

        return StartupState(
            startup_idea="Custom university T-shirt business",
            selling_price=6,
            cost_per_sale=4,
            monthly_fixed_costs=300,
            expected_sales=80,
            constraints=args.constraint,
            max_price=7 if args.max_price is None else args.max_price,
            max_revisions=args.max_revisions,
        )

    if not args.idea.strip():
        parser.error("--idea cannot be blank.")

    missing = [
        name for name, value in financial_inputs.items()
        if value is None
    ]
    if missing:
        parser.error(
            "A custom idea requires these inputs: " + ", ".join(missing)
        )

    if args.selling_price <= 0:
        parser.error("--selling-price must be greater than zero.")
    if args.cost_per_sale < 0:
        parser.error("--cost-per-sale cannot be negative.")
    if args.monthly_fixed_costs < 0:
        parser.error("--monthly-fixed-costs cannot be negative.")
    if args.expected_sales < 0:
        parser.error("--expected-sales cannot be negative.")
    if args.max_price is not None and args.max_price <= 0:
        parser.error("--max-price must be greater than zero.")

    return StartupState(
        startup_idea=args.idea,
        selling_price=args.selling_price,
        cost_per_sale=args.cost_per_sale,
        monthly_fixed_costs=args.monthly_fixed_costs,
        expected_sales=args.expected_sales,
        constraints=args.constraint,
        max_price=args.max_price,
        max_revisions=args.max_revisions,
    )


def main() -> None:
    load_dotenv()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    initial_state = get_initial_state()

    print("Initial state:")
    print(initial_state.model_dump_json(indent=2))

    result = graph.invoke(
        initial_state.model_dump(),
        config={"configurable": {"thread_id": str(uuid4())}},
    )

    print("\nFinal result:")
    print(f"Target customer: {result['target_customer']}")
    print(f"Launch strategy: {result['launch_strategy']}")
    print(f"Proposed price: {result['proposed_price']}")
    print(f"Proposed sales: {result['proposed_sales']}")
    print(f"Added costs: {result['added_costs']}")
    print(f"Unpriced paid actions: {result['unpriced_paid_actions']}")
    print(
        "Total monthly fixed costs: "
        f"{result['total_monthly_fixed_costs']}"
    )
    print(f"Total cost per sale: {result['total_cost_per_sale']}")
    print(f"Break-even sales: {result['break_even_sales']}")
    print(f"Expected profit: {result['expected_profit']:.2f}")
    print(f"Risks: {result['risks']}")
    print(f"Approved: {result['approved']}")
    print(f"Revision count: {result['revision_count']}")


if __name__ == "__main__":
    main()