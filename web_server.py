"""Local browser UI for the startup launch stress tester."""

import json
import math
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from graph import graph
from state import StartupState


WEB_DIR = Path(__file__).resolve().parent / "web"
MAX_REQUEST_BYTES = 16_384


def validate_inputs(data: object) -> StartupState:
    if not isinstance(data, dict):
        raise ValueError("Send a JSON object with the startup details.")

    idea = data.get("startup_idea")
    if not isinstance(idea, str) or not idea.strip() or len(idea) > 1000:
        raise ValueError("Describe your startup idea in 1–1000 characters.")

    numbers = {}
    for name in ("selling_price", "cost_per_sale", "monthly_fixed_costs"):
        value = data.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a number.")
        if value < 0 or (name == "selling_price" and value == 0):
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be {('positive' if name == 'selling_price' else 'non-negative')}.")
        numbers[name] = value

    sales = data.get("expected_sales")
    if isinstance(sales, bool) or not isinstance(sales, int) or sales < 0:
        raise ValueError("Expected sales must be a non-negative whole number.")

    maximum = data.get("max_price")
    if maximum is not None:
        if isinstance(maximum, bool) or not isinstance(maximum, (int, float)) or not math.isfinite(maximum) or maximum <= 0:
            raise ValueError("Maximum price must be a positive number or empty.")

    constraints = data.get("constraints", [])
    if not isinstance(constraints, list) or len(constraints) > 10 or any(not isinstance(item, str) or len(item) > 500 for item in constraints):
        raise ValueError("Provide up to 10 short text constraints.")

    return StartupState(
        startup_idea=idea.strip(),
        selling_price=numbers["selling_price"],
        cost_per_sale=numbers["cost_per_sale"],
        monthly_fixed_costs=numbers["monthly_fixed_costs"],
        expected_sales=sales,
        max_price=maximum,
        constraints=[item.strip() for item in constraints if item.strip()],
    )


def analyze(data: object) -> dict:
    state = validate_inputs(data)
    result = graph.invoke(
        state.model_dump(),
        config={"configurable": {"thread_id": str(uuid4())}},
    )
    return {
        key: result.get(key)
        for key in (
            "startup_idea", "target_customer", "launch_strategy", "proposed_price",
            "proposed_sales", "added_costs", "total_monthly_fixed_costs",
            "total_cost_per_sale", "break_even_sales", "expected_profit",
            "risks", "warnings", "approved", "revision_count", "unpriced_paid_actions",
        )
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        body = (WEB_DIR / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid request length."})
            return
        if length < 1 or length > MAX_REQUEST_BYTES:
            self.send_json(413, {"error": "Request is empty or too large."})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            result = analyze(payload)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})
            return
        except Exception:
            traceback.print_exc()
            self.send_json(500, {"error": "Analysis could not finish. Check the server terminal and try again."})
            return
        self.send_json(200, result)


def main() -> None:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("LaunchLab is running at http://127.0.0.1:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
