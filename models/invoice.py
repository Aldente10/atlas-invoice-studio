from dataclasses import dataclass, field


INVOICE_STATUSES = (
    "Draft",
    "Sent",
    "Partially Paid",
    "Paid",
    "Past Due",
    "Cancelled",
)


@dataclass(slots=True)
class InvoiceItem:
    description: str
    quantity: float = 1.0
    rate_cents: int = 0
    amount_cents: int = 0
    id: int | None = None


@dataclass(slots=True)
class Invoice:
    invoice_number: int
    customer_id: int
    invoice_date: str
    due_date: str
    job_address: str = ""
    notes: str = ""
    subtotal_cents: int = 0
    tax_rate: float = 0.0
    tax_cents: int = 0
    total_cents: int = 0
    status: str = "Draft"
    source_estimate_id: int | None = None
    items: list[InvoiceItem] = field(default_factory=list)
    id: int | None = None
