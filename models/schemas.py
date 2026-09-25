from pydantic import BaseModel, Field


class LaunchStrategyOutput(BaseModel):
    target_customer: str = Field(
        description="The main customer group for this startup."
    )
    launch_strategy: str = Field(
        description="A practical launch plan that respects constraints and addresses risks."
    )
    proposed_price: float = Field(
        gt=0,
        description="Recommended selling price per sale."
    )
    proposed_sales: int = Field(
        ge=0,
        description="Realistic expected sales for one month."
    )
