from pathlib import Path

from models.customer import Customer
from models.invoice import Invoice
from pdf.estimate_pdf import _generate_document_pdf


def generate_invoice_pdf(
    invoice: Invoice,
    customer: Customer,
    company: dict[str, str] | None = None,
) -> Path:
    return _generate_document_pdf(
        invoice,
        customer,
        "INVOICE",
        invoice.invoice_number,
        invoice.invoice_date,
        "Due date",
        invoice.due_date,
        company,
    )
