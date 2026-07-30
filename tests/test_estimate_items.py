from models.service import Service
from services.estimate_items import estimate_item_from_service


def test_service_converts_to_estimate_item() -> None:
    service = Service(
        name="Interior Painting",
        category="Painting",
        description=(
            "Protect floors and furniture.\n"
            "Prepare wall surfaces.\n"
            "Apply two finish coats."
        ),
        default_quantity=2.0,
        default_rate_cents=45000,
        taxable=False,
        favorite=True,
    )

    item = estimate_item_from_service(service)

    assert item.description == (
        "Interior Painting\n"
        "Protect floors and furniture.\n"
        "Prepare wall surfaces.\n"
        "Apply two finish coats."
    )
    assert item.quantity == 2.0
    assert item.rate_cents == 45000
    assert item.amount_cents == 90000


def test_service_without_description_uses_name_only() -> None:
    service = Service(
        name="Service Call",
        default_quantity=1.0,
        default_rate_cents=9500,
    )

    item = estimate_item_from_service(service)

    assert item.description == "Service Call"
    assert item.quantity == 1.0
    assert item.rate_cents == 9500
    assert item.amount_cents == 9500


def test_fractional_quantity_rounds_amount_to_nearest_cent() -> None:
    service = Service(
        name="Hourly Labor",
        default_quantity=1.25,
        default_rate_cents=9999,
    )

    item = estimate_item_from_service(service)

    assert item.amount_cents == round(1.25 * 9999)
