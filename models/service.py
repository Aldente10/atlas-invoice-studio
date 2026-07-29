from dataclasses import dataclass


@dataclass(slots=True)
class Service:
    name: str
    category: str = ""
    description: str = ""
    default_quantity: float = 1.0
    default_rate_cents: int = 0
    taxable: bool = False
    favorite: bool = False
    active: bool = True
    id: int | None = None
