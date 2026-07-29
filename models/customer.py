from dataclasses import dataclass


@dataclass(slots=True)
class Customer:
    name: str
    company: str = ""
    phone: str = ""
    email: str = ""
    billing_address: str = ""
    job_address: str = ""
    notes: str = ""
    id: int | None = None
