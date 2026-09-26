import sys
from textwrap import shorten
from uuid import uuid4

from dotenv import load_dotenv

from graph import graph
from state import StartupState


def print_list(items: list[str], label: str) -> None:
    if not items:
        print(f"{label}: None")
        return

    print(f"{label}:")
    for item in items:
        print(f"  - {item}")


def run_scenario(title: str, initial_state: StartupState) -> None:
    print(f"\n=== {title} ===", flush=True)
    print(f"Startup idea: {initial_state.startup_idea}")
    print(f"Maximum revisions: {initial_state.max_revisions}")
    print_list(initial_state.constraints, "Constraints")
    print("Running graph...", flush=True)

    config = {"configurable": {"thread_id": str(uuid4())}}

    for update in graph.stream(
        initial_state.model_dump(),
        config=config,
        stream_mode="updates",
    ):
        for node, values in update.items():
            if node == "strategist":
                print("\n=== LAUNCH STRATEGIST ===")
                print(
                    "Target customer: "
                    f"{shorten(values['target_customer'], width=160)}"
                )
                print(
                    "Strategy preview: "
                    f"{shorten(values['launch_strategy'], width=200)}"
                )
                print(f"Proposed price: {values['proposed_price']}")
                print(f"Proposed sales: {values['proposed_sales']}")
                print(f"Added costs: {values['added_costs']}")
                print(
                    "Unpriced paid actions: "
                    f"{values['unpriced_paid_actions']}"
                )

            elif node == "financial_analyst":
                print("\n=== FINANCIAL ANALYST ===")
                print(f"Break-even sales: {values['break_even_sales']}")
                print(f"Expected profit: {values['expected_profit']:.2f}")
                print(
                    "Total monthly fixed costs: "
                    f"{values['total_monthly_fixed_costs']}"
                )
                print(
                    "Total cost per sale: "
                    f"{values['total_cost_per_sale']}"
                )

            elif node == "risk_reviewer":
                print("\n=== RISK REVIEWER ===")
                print_list(values["risks"], "Risks")
                print(f"Approved: {values['approved']}")

            elif node == "revise":
                print("\n=== REVISION ===")
                print(f"Revision count: {values['revision_count']}")

            sys.stdout.flush()

    # Reading the state with the same thread_id demonstrates checkpointing.
    final_state = graph.get_state(config).values

    print("\n=== FINAL CHECKPOINT ===")
    print(f"Checkpoint available: {bool(final_state)}")
    print(f"Approved: {final_state['approved']}")
    print(f"Revision count: {final_state['revision_count']}")
    print(f"Final proposed price: {final_state['proposed_price']}")
    print(f"Final expected profit: {final_state['expected_profit']:.2f}")
    print_list(final_state["risks"], "Final risks")
    sys.stdout.flush()


def main() -> None:
    load_dotenv()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # This scenario ends after its first review, whether approved or rejected.
    mugs = StartupState(
        startup_idea="Custom printed mug business",
        selling_price=12,
        cost_per_sale=5,
        monthly_fixed_costs=300,
        expected_sales=80,
        constraints=[],
        max_price=15,
        max_revisions=0,
    )
    run_scenario("SCENARIO 1: MUGS - END AFTER FIRST REVIEW", mugs)

    # A free-text constraint requires manual verification. It therefore
    # triggers a revision, then ends when the revision limit is reached.
    shirts = StartupState(
        startup_idea="Custom university T-shirt business",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        constraints=["Launch must use biodegradable packaging"],
        max_price=7,
        max_revisions=1,
    )
    run_scenario("SCENARIO 2: SHIRTS - REVISION PATH", shirts)


if __name__ == "__main__":
    main()