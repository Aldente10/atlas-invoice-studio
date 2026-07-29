from dataclasses import dataclass, field


@dataclass(slots=True)
class EstimateItem:
    description: str
    quantity: float = 1.0
    rate_cents: int = 0
    amount_cents: int = 0
    id: int | None = None


@dataclass(slots=True)
class Estimate:
    estimate_number: int
    customer_id: int
    estimate_date: str
    expiration_date: str
    job_address: str = ""
    notes: str = ""
    subtotal_cents: int = 0
    tax_rate: float = 0.0
    tax_cents: int = 0
    total_cents: int = 0
    status: str = "Draft"
    items: list[EstimateItem] = field(default_factory=list)
    id: int | None = None
