from datetime import date

import pytest

from database import database
from database.customer_repository import CustomerRepository
from database.estimate_repository import EstimateRepository
from database.invoice_repository import (
    DuplicateEstimateConversionError,
    InvoiceRepository,
)
from models.customer import Customer
from models.estimate import Estimate, EstimateItem


@pytest.fixture
def repositories(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "test.db")
    database.initialize_database()
    return CustomerRepository(), EstimateRepository(), InvoiceRepository()


def saved_estimate(customer_repository, estimate_repository) -> Estimate:
    customer = customer_repository.create(
        Customer(name="Taylor Reed", job_address="18 Ocean Pine Way")
    )
    return estimate_repository.create(
        Estimate(
            estimate_number=8125,
            customer_id=customer.id,
            estimate_date="2026-07-20",
            expiration_date="2026-08-03",
            job_address="44 Harbor View Drive",
            notes="Materials and labor included.",
            subtotal_cents=24750,
            tax_rate=7.0,
            tax_cents=1733,
            total_cents=26483,
            items=[
                EstimateItem(
                    description="Cabinet refinishing",
                    quantity=1.5,
                    rate_cents=16500,
                    amount_cents=24750,
                )
            ],
        )
    )


def test_estimate_to_invoice_preserves_business_details(repositories) -> None:
    customers, estimates, invoices = repositories
    estimate = saved_estimate(customers, estimates)

    invoice = invoices.create_from_estimate(
        estimate, invoice_date=date(2026, 7, 30)
    )
    loaded = invoices.get_by_id(invoice.id)

    assert loaded is not None
    assert loaded.source_estimate_id == estimate.id
    assert loaded.customer_id == estimate.customer_id
    assert loaded.invoice_date == "2026-07-30"
    assert loaded.due_date == "2026-08-29"
    assert loaded.job_address == estimate.job_address
    assert loaded.notes == estimate.notes
    assert loaded.subtotal_cents == estimate.subtotal_cents
    assert loaded.tax_rate == estimate.tax_rate
    assert loaded.tax_cents == estimate.tax_cents
    assert loaded.total_cents == estimate.total_cents
    assert loaded.status == "Draft"
    assert [
        (item.description, item.quantity, item.rate_cents, item.amount_cents)
        for item in loaded.items
    ] == [
        (item.description, item.quantity, item.rate_cents, item.amount_cents)
        for item in estimate.items
    ]


def test_invoice_numbering_is_independent_from_estimates(repositories) -> None:
    customers, estimates, invoices = repositories
    estimate = saved_estimate(customers, estimates)

    assert estimates.next_estimate_number() == 8126
    assert invoices.next_invoice_number() == 1001

    first_invoice = invoices.create_from_estimate(estimate)

    assert first_invoice.invoice_number == 1001
    assert invoices.next_invoice_number() == 1002


def test_duplicate_conversion_requires_explicit_override(repositories) -> None:
    customers, estimates, invoices = repositories
    estimate = saved_estimate(customers, estimates)
    invoices.create_from_estimate(estimate)

    with pytest.raises(DuplicateEstimateConversionError):
        invoices.create_from_estimate(estimate)

    duplicate = invoices.create_from_estimate(estimate, allow_duplicate=True)

    assert duplicate.invoice_number == 1002
    assert duplicate.source_estimate_id == estimate.id
