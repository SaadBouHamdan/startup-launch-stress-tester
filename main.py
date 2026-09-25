from dotenv import load_dotenv

from graph import graph
from state import StartupState


def main():
    load_dotenv()

    initial_state = StartupState(
        startup_idea="Custom university T-shirt business",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        constraints=[],
        max_price=7,
    )

    print("Initial state:")
    print(initial_state.model_dump_json(indent=2))

    result = graph.invoke(
        initial_state.model_dump(),
        config={"configurable": {"thread_id": "startup-demo-1"}},
    )

    print("\nFinal result:")
    print(f"Target customer: {result['target_customer']}")
    print(f"Launch strategy: {result['launch_strategy']}")
    print(f"Proposed price: {result['proposed_price']}")
    print(f"Proposed sales: {result['proposed_sales']}")
    print(f"Break-even sales: {result['break_even_sales']}")
    print(f"Expected profit: {result['expected_profit']}")
    print(f"Risks: {result['risks']}")
    print(f"Approved: {result['approved']}")
    print(f"Revision count: {result['revision_count']}")


if __name__ == "__main__":
    main()
