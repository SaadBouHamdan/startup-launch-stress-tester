from pydantic import BaseModel, Field


class AddedCost(BaseModel):
    description: str = Field(
        min_length=1,
        description="What the added expense pays for.",
    )
    monthly_fixed: float = Field(
        default=0,
        ge=0,
        allow_inf_nan=False,
        description=(
            "New monthly cost, excluding amounts already included "
            "in monthly_fixed_costs."
        ),
    )
    per_sale: float = Field(
        default=0,
        ge=0,
        allow_inf_nan=False,
        description=(
            "New cost per sale, excluding amounts already included "
            "in cost_per_sale."
        ),
    )


class LaunchStrategyOutput(BaseModel):
    target_customer: str = Field(
        description="The main customer group for this startup."
    )
    launch_strategy: str = Field(
        description="A practical launch plan that respects constraints and addresses risks."
    )
    proposed_price: float = Field(
        gt=0,
        description="Recommended selling price per sale.",
    )
    proposed_sales: int = Field(
        ge=0,
        description="Realistic expected sales for one month.",
    )
    added_costs: list[AddedCost] = Field(
        default_factory=list,
        description=(
            "All new paid actions in the strategy, with estimated "
            "monthly fixed or per-sale costs."
        ),
    )
    unpriced_paid_actions: list[str] = Field(
        default_factory=list,
        description=(
            "Paid actions without a reliable cost estimate; these prevent "
            "automatic approval."
        ),
    )