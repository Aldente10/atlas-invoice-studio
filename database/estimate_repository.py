from database.database import get_connection
from models.estimate import Estimate


class EstimateRepository:
    def next_estimate_number(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT COALESCE(MAX(estimate_number), 1038) + 1 AS next_number
                FROM estimates
                """
            ).fetchone()

        return int(row["next_number"])

    def create(self, estimate: Estimate) -> Estimate:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO estimates (
                    estimate_number,
                    customer_id,
                    estimate_date,
                    expiration_date,
                    job_address,
                    notes,
                    subtotal_cents,
                    tax_rate,
                    tax_cents,
                    total_cents,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    estimate.estimate_number,
                    estimate.customer_id,
                    estimate.estimate_date,
                    estimate.expiration_date,
                    estimate.job_address.strip(),
                    estimate.notes.strip(),
                    estimate.subtotal_cents,
                    estimate.tax_rate,
                    estimate.tax_cents,
                    estimate.total_cents,
                    estimate.status,
                ),
            )

            estimate.id = cursor.lastrowid

            for position, item in enumerate(estimate.items):
                connection.execute(
                    """
                    INSERT INTO estimate_items (
                        estimate_id,
                        position,
                        description,
                        quantity,
                        rate_cents,
                        amount_cents
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        estimate.id,
                        position,
                        item.description.strip(),
                        item.quantity,
                        item.rate_cents,
                        item.amount_cents,
                    ),
                )

        return estimate
