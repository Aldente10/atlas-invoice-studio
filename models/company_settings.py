from dataclasses import dataclass, asdict


@dataclass(slots=True)
class CompanySettings:
    business_name: str = ""
    contact_name: str = ""
    street_address: str = ""
    city_state_zip: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    license_number: str = ""
    logo_path: str = ""
    default_estimate_notes: str = "Materials and labor included."
    default_invoice_notes: str = "Thank you for your business."
    estimate_expiration_days: int = 14
    next_estimate_number: int = 1039
    next_invoice_number: int = 1001

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)
