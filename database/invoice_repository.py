from datetime import date, timedelta

from database.database import get_connection
from models.estimate import Estimate
from models.invoice import INVOICE_STATUSES, Invoice, InvoiceItem


class DuplicateEstimateConversionError(ValueError):
    """Raised when an estimate already has at least one invoice."""


class InvoiceRepository:
    def next_invoice_number(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT MAX(
                    COALESCE(MAX(invoice_number), 1000) + 1,
                    COALESCE(
                        (SELECT next_invoice_number
                         FROM company_settings WHERE id = 1),
                        1001
                    )
                ) AS next_number
                FROM invoices
                """
            ).fetchone()

        return int(row["next_number"])

    def create(self, invoice: Invoice) -> Invoice:
        self._validate(invoice)

        with get_connection() as connection:
            invoice.id = self._insert(connection, invoice)
            self._insert_items(connection, invoice)

        return invoice

    def create_from_estimate(
        self,
        estimate: Estimate,
        *,
        allow_duplicate: bool = False,
        invoice_date: date | None = None,
    ) -> Invoice:
        if estimate.id is None:
            raise ValueError("Only a saved estimate can be converted.")

        issued_on = invoice_date or date.today()

        with get_connection() as connection:
            existing = connection.execute(
                """
                SELECT invoice_number
                FROM invoices
                WHERE source_estimate_id = ?
                ORDER BY invoice_number
                """,
                (estimate.id,),
            ).fetchall()

            if existing and not allow_duplicate:
                numbers = ", ".join(str(row["invoice_number"]) for row in existing)
                raise DuplicateEstimateConversionError(
                    f"Estimate #{estimate.estimate_number} was already converted "
                    f"to invoice #{numbers}."
                )

            number_row = connection.execute(
                """
                SELECT MAX(
                    COALESCE(MAX(invoice_number), 1000) + 1,
                    COALESCE(
                        (SELECT next_invoice_number
                         FROM company_settings WHERE id = 1),
                        1001
                    )
                ) AS next_number
                FROM invoices
                """
            ).fetchone()

            invoice = Invoice(
                invoice_number=int(number_row["next_number"]),
                customer_id=estimate.customer_id,
                source_estimate_id=estimate.id,
                invoice_date=issued_on.isoformat(),
                due_date=(issued_on + timedelta(days=30)).isoformat(),
                job_address=estimate.job_address,
                notes=estimate.notes,
                subtotal_cents=estimate.subtotal_cents,
                tax_rate=estimate.tax_rate,
                tax_cents=estimate.tax_cents,
                total_cents=estimate.total_cents,
                status="Draft",
                items=[
                    InvoiceItem(
                        description=item.description,
                        quantity=item.quantity,
                        rate_cents=item.rate_cents,
                        amount_cents=item.amount_cents,
                    )
                    for item in estimate.items
                ],
            )
            self._validate(invoice)
            invoice.id = self._insert(connection, invoice)
            self._insert_items(connection, invoice)

        return invoice

    def update(self, invoice: Invoice) -> None:
        if invoice.id is None:
            raise ValueError("Cannot update an invoice without an ID.")
        self._validate(invoice)

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE invoices
                SET invoice_number = ?, customer_id = ?, invoice_date = ?,
                    due_date = ?, job_address = ?, notes = ?,
                    subtotal_cents = ?, tax_rate = ?, tax_cents = ?,
                    total_cents = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    invoice.invoice_number,
                    invoice.customer_id,
                    invoice.invoice_date,
                    invoice.due_date,
                    invoice.job_address.strip(),
                    invoice.notes.strip(),
                    invoice.subtotal_cents,
                    invoice.tax_rate,
                    invoice.tax_cents,
                    invoice.total_cents,
                    invoice.status,
                    invoice.id,
                ),
            )
            connection.execute(
                "DELETE FROM invoice_items WHERE invoice_id = ?",
                (invoice.id,),
            )
            self._insert_items(connection, invoice)

    def get_by_id(self, invoice_id: int) -> Invoice | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, invoice_number, customer_id, source_estimate_id,
                       invoice_date, due_date, job_address, notes,
                       subtotal_cents, tax_rate, tax_cents, total_cents, status
                FROM invoices
                WHERE id = ?
                """,
                (invoice_id,),
            ).fetchone()
            if row is None:
                return None

            item_rows = connection.execute(
                """
                SELECT id, description, quantity, rate_cents, amount_cents
                FROM invoice_items
                WHERE invoice_id = ?
                ORDER BY position
                """,
                (invoice_id,),
            ).fetchall()

        return Invoice(
            id=row["id"],
            invoice_number=row["invoice_number"],
            customer_id=row["customer_id"],
            source_estimate_id=row["source_estimate_id"],
            invoice_date=row["invoice_date"],
            due_date=row["due_date"],
            job_address=row["job_address"],
            notes=row["notes"],
            subtotal_cents=row["subtotal_cents"],
            tax_rate=row["tax_rate"],
            tax_cents=row["tax_cents"],
            total_cents=row["total_cents"],
            status=row["status"],
            items=[
                InvoiceItem(
                    id=item["id"],
                    description=item["description"],
                    quantity=item["quantity"],
                    rate_cents=item["rate_cents"],
                    amount_cents=item["amount_cents"],
                )
                for item in item_rows
            ],
        )

    def get_all_summaries(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT invoices.id, invoices.invoice_number,
                       invoices.invoice_date, invoices.total_cents,
                       invoices.status, customers.name AS customer_name,
                       customers.company AS customer_company
                FROM invoices
                JOIN customers ON customers.id = invoices.customer_id
                ORDER BY invoices.invoice_number DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def delete(self, invoice_id: int) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))

    @staticmethod
    def _validate(invoice: Invoice) -> None:
        if invoice.status not in INVOICE_STATUSES:
            raise ValueError(f"Unsupported invoice status: {invoice.status}")

    @staticmethod
    def _insert(connection, invoice: Invoice) -> int:
        cursor = connection.execute(
            """
            INSERT INTO invoices (
                invoice_number, customer_id, source_estimate_id, invoice_date,
                due_date, job_address, notes, subtotal_cents, tax_rate,
                tax_cents, total_cents, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice.invoice_number,
                invoice.customer_id,
                invoice.source_estimate_id,
                invoice.invoice_date,
                invoice.due_date,
                invoice.job_address.strip(),
                invoice.notes.strip(),
                invoice.subtotal_cents,
                invoice.tax_rate,
                invoice.tax_cents,
                invoice.total_cents,
                invoice.status,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _insert_items(connection, invoice: Invoice) -> None:
        if invoice.id is None:
            raise ValueError("Invoice must have an ID before adding items.")
        for position, item in enumerate(invoice.items):
            connection.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, position, description, quantity,
                    rate_cents, amount_cents
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice.id,
                    position,
                    item.description.strip(),
                    item.quantity,
                    item.rate_cents,
                    item.amount_cents,
                ),
            )
