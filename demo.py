import sys
from textwrap import shorten
from uuid import uuid4

from dotenv import load_dotenv

from graph import graph
from state import StartupState


def print_risks(risks: list[str], label: str = "Risks") -> None:
    if not risks:
        print(f"{label}: None")
    else:
        print(f"{label}:")
        for risk in risks:
            print(f"  - {risk}")


def run_scenario(title: str, initial_state: StartupState) -> None:
    print(f"\n=== {title} ===", flush=True)
    print(f"Price cap: {initial_state.max_price}")
    print(f"Maximum revisions: {initial_state.max_revisions}")
    print_risks(initial_state.constraints, "Constraints")
    print("Running graph...", flush=True)
    config = {"configurable": {"thread_id": str(uuid4())}}

    for update in graph.stream(
        initial_state.model_dump(), config=config, stream_mode="updates"
    ):
        for node, values in update.items():
            if node == "strategist":
                print("\n=== LAUNCH STRATEGIST ===")
                print(f"Target customer: {shorten(values['target_customer'], width=160)}")
                print(f"Strategy (preview): {shorten(values['launch_strategy'], width=200)}")
                print(f"Proposed price: {values['proposed_price']}")
                print(f"Proposed sales: {values['proposed_sales']}")
            elif node == "financial_analyst":
                print("\n=== FINANCIAL ANALYST ===")
                print(f"Break-even sales: {values['break_even_sales']}")
                print(f"Expected profit: {values['expected_profit']}")
            elif node == "risk_reviewer":
                print("\n=== RISK REVIEWER ===")
                print_risks(values["risks"])
                print(f"Approved: {values['approved']}")
            elif node == "revise":
                print("\n=== REVISION ===")
                print(f"Revision count: {values['revision_count']}")
            sys.stdout.flush()

    final_state = graph.get_state(config).values
    if final_state["approved"]:
        print("\n=== END: PLAN APPROVED ===")
    else:
        print("\n=== END: REVISION LIMIT REACHED ===")
    print(f"Approved: {final_state['approved']}")
    print(f"Revision count: {final_state['revision_count']}")
    print(f"Final proposed price: {final_state['proposed_price']}")
    print(f"Final expected profit: {final_state['expected_profit']}")
    print_risks(final_state["risks"], "Final risks")
    sys.stdout.flush()


def main() -> None:
    load_dotenv()
    # Allow generated Unicode text to print on Windows consoles.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    initial_state = StartupState(
        startup_idea="Custom university T-shirt business",
        selling_price=6,
        cost_per_sale=4,
        monthly_fixed_costs=300,
        expected_sales=80,
        constraints=[],
        max_price=7,
        max_revisions=3,
    )
    run_scenario("SCENARIO 1: REJECTION → REVISION → APPROVAL", initial_state)

    revision_state = initial_state.model_copy(update={
        "constraints": ["Launch must use biodegradable packaging"],
        "max_revisions": 1,
    })
    run_scenario("SCENARIO 2: REVISION LIMIT REACHED", revision_state)


if __name__ == "__main__":
    main()
