from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.financial_analyst import financial_analyst
from agents.risk_reviewer import risk_reviewer
from agents.strategist import launch_strategist
from state import StartupState


def route_after_review(state: StartupState) -> str:
    if state.approved:
        return "end"

    if state.revision_count < state.max_revisions:
        return "revise"

    return "end"


def increment_revision(state: StartupState) -> dict:
    return {"revision_count": state.revision_count + 1}


builder = StateGraph(StartupState)

builder.add_node("strategist", launch_strategist)
builder.add_node("financial_analyst", financial_analyst)
builder.add_node("risk_reviewer", risk_reviewer)
builder.add_node("revise", increment_revision)

builder.add_edge(START, "strategist")
builder.add_edge("strategist", "financial_analyst")
builder.add_edge("financial_analyst", "risk_reviewer")

builder.add_conditional_edges(
    "risk_reviewer",
    route_after_review,
    {
        "end": END,
        "revise": "revise",
    },
)

builder.add_edge("revise", "strategist")

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
