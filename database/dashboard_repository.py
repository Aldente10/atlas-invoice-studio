from dataclasses import dataclass
from datetime import date

from database.database import get_connection


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    customer_count: int
    open_estimate_count: int
    open_estimate_total_cents: int
    unpaid_invoice_count: int
    unpaid_invoice_total_cents: int
    paid_this_month_total_cents: int


@dataclass(frozen=True, slots=True)
class RecentDocument:
    document_type: str
    document_id: int
    document_number: int
    document_date: str
    customer_name: str
    customer_company: str
    total_cents: int
    status: str
    updated_at: str


class DashboardRepository:
    def get_summary(self, *, today: date | None = None) -> DashboardSummary:
        current_day = today or date.today()
        month_start = current_day.replace(day=1).isoformat()
        if current_day.month == 12:
            next_month = date(current_day.year + 1, 1, 1)
        else:
            next_month = date(current_day.year, current_day.month + 1, 1)

        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM customers) AS customer_count,
                    (SELECT COUNT(*) FROM estimates AS estimate
                     WHERE status NOT IN ('Accepted', 'Rejected', 'Expired', 'Converted')
                       AND NOT EXISTS (
                           SELECT 1 FROM invoices
                           WHERE source_estimate_id = estimate.id
                       ))
                        AS open_estimate_count,
                    (SELECT COALESCE(SUM(total_cents), 0) FROM estimates AS estimate
                     WHERE status NOT IN ('Accepted', 'Rejected', 'Expired', 'Converted')
                       AND NOT EXISTS (
                           SELECT 1 FROM invoices
                           WHERE source_estimate_id = estimate.id
                       ))
                        AS open_estimate_total_cents,
                    (SELECT COUNT(*) FROM invoices
                     WHERE status NOT IN ('Paid', 'Cancelled'))
                        AS unpaid_invoice_count,
                    (SELECT COALESCE(SUM(total_cents), 0) FROM invoices
                     WHERE status NOT IN ('Paid', 'Cancelled'))
                        AS unpaid_invoice_total_cents,
                    (SELECT COALESCE(SUM(total_cents), 0) FROM invoices
                     WHERE status = 'Paid'
                       AND invoice_date >= ? AND invoice_date < ?)
                        AS paid_this_month_total_cents
                """,
                (month_start, next_month.isoformat()),
            ).fetchone()

        return DashboardSummary(**dict(row))

    def get_recent_documents(self, *, limit: int = 6) -> list[RecentDocument]:
        if limit < 1:
            return []

        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT document_type, document_id, document_number,
                       document_date, customer_name, customer_company,
                       total_cents, status, updated_at
                FROM (
                    SELECT 'Estimate' AS document_type,
                           estimates.id AS document_id,
                           estimates.estimate_number AS document_number,
                           estimates.estimate_date AS document_date,
                           customers.name AS customer_name,
                           customers.company AS customer_company,
                           estimates.total_cents AS total_cents,
                           estimates.status AS status,
                           estimates.updated_at AS updated_at
                    FROM estimates
                    JOIN customers ON customers.id = estimates.customer_id
                    UNION ALL
                    SELECT 'Invoice' AS document_type,
                           invoices.id AS document_id,
                           invoices.invoice_number AS document_number,
                           invoices.invoice_date AS document_date,
                           customers.name AS customer_name,
                           customers.company AS customer_company,
                           invoices.total_cents AS total_cents,
                           invoices.status AS status,
                           invoices.updated_at AS updated_at
                    FROM invoices
                    JOIN customers ON customers.id = invoices.customer_id
                )
                ORDER BY updated_at DESC, document_type ASC,
                         document_number DESC, document_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [RecentDocument(**dict(row)) for row in rows]
