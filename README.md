# Startup Launch Stress Tester

## Project Overview

Startup Launch Stress Tester is a COE 549 group project that evaluates a startup launch plan using an LLM and deterministic financial checks. It proposes a strategy, calculates financial results, identifies risks, and revises rejected plans within a configured limit.

Approval means the plan passes the implemented checks; it is not a guarantee of business success. Extra costs are estimates supplied by the Strategist, not verified market prices. A person should check whether the written strategy omits a paid action; the deterministic Reviewer can only reject paid actions that are declared without a cost estimate.

## How the System Works

1. Provide a startup idea, selling price, cost per sale, monthly fixed costs, expected monthly sales, and constraints.
2. The Launch Strategist proposes a target customer, launch strategy, price, and sales estimate.
3. The Financial Analyst calculates break-even sales and expected profit, including new monthly and per-sale expenses listed by the Strategist.
4. The Risk Reviewer checks the financial results, constraints, and declared paid actions without estimates.
5. The graph ends on approval or revises the proposal until the revision limit is reached.

The optional `max_price` input sets a price cap. A proposal above it is rejected; equality is allowed. When the cap is `None`, no cap check applies. Nonblank free-text constraints require manual verification and prevent automatic approval.

The Strategist lists incremental expenses in `added_costs` and expenses needing an estimate in `unpriced_paid_actions`. Existing costs must not be listed again. A proposal with an unpriced paid action cannot be automatically approved.

## Agent Roles

| Agent | Responsibility | Model or toolset |
| --- | --- | --- |
| Launch Strategist | Create and revise a realistic launch proposal using previous reviewer feedback. | OpenAI through `ChatOpenAI`, with the Pydantic `LaunchStrategyOutput` schema. |
| Financial Analyst | Calculate break-even and profit using base costs plus itemized incremental expenses. | `calculate_break_even_tool`, `calculate_profit_tool`. |
| Risk Reviewer | Validate financial values, profit, break-even coverage, price limits, constraints, and declared unpriced paid actions. | `check_financial_risks`, `check_manual_constraints`. |

The Financial Analyst and Risk Reviewer have different, non-overlapping LangChain toolsets. Both invoke their tools explicitly and deterministically; neither uses an LLM.

## Architecture / Workflow

`graph.py` builds a LangGraph `StateGraph(StartupState)`. Each node returns a partial state update. `MemorySaver` checkpoints execution using a `thread_id`; checkpoints remain in memory only and do not survive a process restart.

```text
START
  ↓
Launch Strategist
  ↓
Financial Analyst
  ↓
Risk Reviewer
  ↓
Approved?
  ├── Yes → END
  └── No
       ├── Revisions available → Revise → Launch Strategist
       └── Revision limit reached → END (not approved)
```

The `revise` node increments `revision_count` before returning to the Strategist. With `max_revisions=3`, execution permits one initial attempt and up to three revisions. Exceptions raised by nodes propagate rather than triggering this review loop.

## Project Requirements / Dependencies

- Python (the project has been tested with Python 3.13).
- Git for cloning and version control.
- An OpenAI API key with access to the configured `gpt-5-mini` model for live runs.
- Packages in `requirements.txt`: `langgraph`, `langchain`, `langchain-openai`, `pydantic`, `python-dotenv`, and `pytest`.

## Setup Instructions

Clone the repository and create a virtual environment:

```shell
git clone https://github.com/SaadBouHamdan/startup-launch-stress-tester.git
cd startup-launch-stress-tester
python -m venv .venv
```

Activate the virtual environment on Windows Command Prompt:

```bat
.venv\Scripts\activate
```

For Windows PowerShell, use:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```shell
pip install -r requirements.txt
```

## Environment Variables

Each user must create a local `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_key_here
```

Replace the placeholder with your own API key. `main.py` loads the file using `load_dotenv()`.

**Do not commit `.env` or share API keys.** The project's `.gitignore` already excludes `.env`. Live runs require internet access and may incur OpenAI API charges.

## How to Run

With the virtual environment active, run:

```shell
python main.py
```

The current demo evaluates a custom university T-shirt business with a selling price of 6, cost per sale of 4, monthly fixed costs of 300, expected sales of 80, and `max_price=7`. It prints the initial state, final proposal, financial results, risks, approval status, and revision count. It also prints incremental expenses and the total costs used in the financial calculation.

Run the expanded demo to see partial updates from each graph node and two scenarios:

```shell
python demo.py
```

A live proposal may pass on the first attempt, so a revision is not guaranteed. Mocked graph tests demonstrate both successful revision and termination after repeated rejection.

If the Windows console cannot print Unicode characters in the generated strategy, use:

```shell
python -X utf8 main.py
```

## Browser UI

From the repository folder, run the local web server with your virtual environment:

```powershell
.\.venv\Scripts\python.exe web_server.py
```

Open `http://127.0.0.1:8000` in a browser. The conversation asks for the idea, price, cost per sale, monthly fixed costs, expected sales, an optional maximum price, and optional constraints one at a time. After the final answer, the existing LangGraph workflow runs and the page shows its strategy, financial results, risks, and approval status. Use **New stress test** to try another idea. The server binds to localhost and loads `OPENAI_API_KEY` from `.env` on the server; the browser never receives the key. Live runs require network access and may incur API charges.

## How to Run Tests

With the virtual environment active, run:

```shell
python -m pytest
```

The suite has **60 passing tests**. Tests mock OpenAI model calls, require no real API key, and make no live OpenAI requests. Coverage includes financial calculations, added expenses, unpriced paid actions, distinct toolsets, reviewer checks, structured-output handling, price caps, routing, and revision limits.

## Project Structure

```text
startup-launch-stress-tester/
├── main.py                   # Demo entry point
├── web_server.py             # Local HTTP API and frontend server
├── web/index.html            # Guided browser interface
├── graph.py                  # LangGraph nodes, routing, and checkpointing
├── state.py                  # Shared Pydantic StartupState
├── agents/
│   ├── strategist.py         # LLM launch planning
│   ├── financial_analyst.py  # Financial tool invocation
│   └── risk_reviewer.py      # Risk tool invocation and approval
├── tools/
│   ├── financial_tools.py    # Calculation helpers and LangChain wrappers
│   └── risk_tools.py         # Deterministic validation tools
├── models/
│   └── schemas.py            # LaunchStrategyOutput and AddedCost
├── tests/                    # Unit and mocked graph tests
├── requirements.txt
├── .gitignore
├── .env.example              # Example environment-variable template
└── README.md
```

## Current Status

- Three agent nodes and two distinct explicit toolsets are implemented.
- Structured LLM output, deterministic calculations, and price-cap validation are implemented.
- Incremental strategy costs are included in profit and break-even calculations.
- Declared paid actions without cost estimates block approval.
- Conditional revision routing and in-memory checkpointing are implemented.
- Mocked graph tests verify approval after revision and stopping at the revision limit.
- All 60 tests pass.
