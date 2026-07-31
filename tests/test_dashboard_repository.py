from datetime import date

import pytest

from database import database
from database.customer_repository import CustomerRepository
from database.dashboard_repository import DashboardRepository
from database.estimate_repository import EstimateRepository
from database.invoice_repository import InvoiceRepository
from models.customer import Customer
from models.estimate import Estimate
from models.invoice import Invoice


@pytest.fixture
def dashboard_data(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "dashboard.db")
    database.initialize_database()
    customer = CustomerRepository().create(Customer(name="Danny Client"))
    return customer, EstimateRepository(), InvoiceRepository(), DashboardRepository()


def save_estimate(repository, customer_id, number, total, status="Draft"):
    return repository.create(
        Estimate(
            estimate_number=number,
            customer_id=customer_id,
            estimate_date="2026-07-20",
            expiration_date="2026-08-03",
            total_cents=total,
            status=status,
        )
    )


def save_invoice(
    repository,
    customer_id,
    number,
    total,
    invoice_date,
    status,
    source_estimate_id=None,
):
    return repository.create(
        Invoice(
            invoice_number=number,
            customer_id=customer_id,
            invoice_date=invoice_date,
            due_date=invoice_date,
            total_cents=total,
            status=status,
            source_estimate_id=source_estimate_id,
        )
    )


def test_dashboard_summary_calculations(dashboard_data) -> None:
    customer, estimates, invoices, dashboard = dashboard_data
    CustomerRepository().create(Customer(name="Second Customer"))
    save_estimate(estimates, customer.id, 2001, 12500)
    save_estimate(estimates, customer.id, 2002, 8000, "Accepted")
    converted = save_estimate(estimates, customer.id, 2003, 7000)
    save_invoice(invoices, customer.id, 3001, 45000, "2026-07-12", "Sent")
    save_invoice(invoices, customer.id, 3002, 12000, "2026-07-13", "Paid")
    save_invoice(invoices, customer.id, 3003, 9000, "2026-06-30", "Paid")
    save_invoice(invoices, customer.id, 3004, 5000, "2026-07-14", "Cancelled")
    save_invoice(
        invoices,
        customer.id,
        3005,
        7000,
        "2026-07-15",
        "Paid",
        source_estimate_id=converted.id,
    )

    summary = dashboard.get_summary(today=date(2026, 7, 30))

    assert summary.customer_count == 2
    assert summary.open_estimate_count == 1
    assert summary.open_estimate_total_cents == 12500
    assert summary.unpaid_invoice_count == 1
    assert summary.unpaid_invoice_total_cents == 45000
    assert summary.paid_this_month_total_cents == 19000


def test_recent_documents_are_ordered_by_latest_update(dashboard_data) -> None:
    customer, estimates, invoices, dashboard = dashboard_data
    older_estimate = save_estimate(estimates, customer.id, 2101, 1000)
    newest_estimate = save_estimate(estimates, customer.id, 2102, 2000)
    middle_invoice = save_invoice(
        invoices, customer.id, 3101, 3000, "2026-07-29", "Draft"
    )
    with database.get_connection() as connection:
        connection.execute(
            "UPDATE estimates SET updated_at = ? WHERE id = ?",
            ("2026-07-28 09:00:00", older_estimate.id),
        )
        connection.execute(
            "UPDATE invoices SET updated_at = ? WHERE id = ?",
            ("2026-07-29 09:00:00", middle_invoice.id),
        )
        connection.execute(
            "UPDATE estimates SET updated_at = ? WHERE id = ?",
            ("2026-07-30 09:00:00", newest_estimate.id),
        )

    recent = dashboard.get_recent_documents(limit=2)

    assert [(item.document_type, item.document_number) for item in recent] == [
        ("Estimate", 2102),
        ("Invoice", 3101),
    ]
