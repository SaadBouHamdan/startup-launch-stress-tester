from typing import Optional

from pydantic import BaseModel, Field

from models.schemas import AddedCost


class StartupState(BaseModel):
    # User inputs
    startup_idea: str
    selling_price: float
    cost_per_sale: float
    monthly_fixed_costs: float
    expected_sales: int
    constraints: list[str] = Field(default_factory=list)
    max_price: Optional[float] = None

    # Strategist outputs
    target_customer: Optional[str] = None
    launch_strategy: Optional[str] = None
    proposed_price: Optional[float] = None
    proposed_sales: Optional[int] = None
    added_costs: list[AddedCost] = Field(default_factory=list)
    unpriced_paid_actions: list[str] = Field(default_factory=list)

    # Financial analyst outputs
    break_even_sales: Optional[float] = None
    expected_profit: Optional[float] = None
    total_monthly_fixed_costs: Optional[float] = None
    total_cost_per_sale: Optional[float] = None

    # Risk reviewer outputs
    risks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    approved: bool = False

    # Graph control
    revision_count: int = 0
    max_revisions: int = 3