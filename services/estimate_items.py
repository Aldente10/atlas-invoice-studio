from models.estimate import EstimateItem
from models.service import Service


def estimate_item_from_service(service: Service) -> EstimateItem:
    """
    Convert a saved service into an editable estimate line item.
    """
    description_parts = [service.name.strip()]

    if service.description.strip():
        description_parts.append(service.description.strip())

    description = "\n".join(description_parts)

    quantity = service.default_quantity
    rate_cents = service.default_rate_cents
    amount_cents = round(quantity * rate_cents)

    return EstimateItem(
        description=description,
        quantity=quantity,
        rate_cents=rate_cents,
        amount_cents=amount_cents,
    )
