from database.database import get_connection
from models.estimate import Estimate, EstimateItem


class EstimateRepository:
    def next_estimate_number(self) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT MAX(
                    COALESCE(MAX(estimate_number), 1038) + 1,
                    COALESCE(
                        (SELECT next_estimate_number
                         FROM company_settings WHERE id = 1),
                        1039
                    )
                ) AS next_number
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
            self._insert_items(connection, estimate)

        return estimate

    def update(self, estimate: Estimate) -> None:
        if estimate.id is None:
            raise ValueError("Cannot update an estimate without an ID.")

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE estimates
                SET
                    estimate_number = ?,
                    customer_id = ?,
                    estimate_date = ?,
                    expiration_date = ?,
                    job_address = ?,
                    notes = ?,
                    subtotal_cents = ?,
                    tax_rate = ?,
                    tax_cents = ?,
                    total_cents = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
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
                    estimate.id,
                ),
            )

            connection.execute(
                "DELETE FROM estimate_items WHERE estimate_id = ?",
                (estimate.id,),
            )

            self._insert_items(connection, estimate)

    def get_by_id(self, estimate_id: int) -> Estimate | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
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
                FROM estimates
                WHERE id = ?
                """,
                (estimate_id,),
            ).fetchone()

            if row is None:
                return None

            item_rows = connection.execute(
                """
                SELECT
                    id,
                    description,
                    quantity,
                    rate_cents,
                    amount_cents
                FROM estimate_items
                WHERE estimate_id = ?
                ORDER BY position
                """,
                (estimate_id,),
            ).fetchall()

        return Estimate(
            id=row["id"],
            estimate_number=row["estimate_number"],
            customer_id=row["customer_id"],
            estimate_date=row["estimate_date"],
            expiration_date=row["expiration_date"],
            job_address=row["job_address"],
            notes=row["notes"],
            subtotal_cents=row["subtotal_cents"],
            tax_rate=row["tax_rate"],
            tax_cents=row["tax_cents"],
            total_cents=row["total_cents"],
            status=row["status"],
            items=[
                EstimateItem(
                    id=item_row["id"],
                    description=item_row["description"],
                    quantity=item_row["quantity"],
                    rate_cents=item_row["rate_cents"],
                    amount_cents=item_row["amount_cents"],
                )
                for item_row in item_rows
            ],
        )

    def get_all_summaries(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    estimates.id,
                    estimates.estimate_number,
                    estimates.estimate_date,
                    estimates.total_cents,
                    estimates.status,
                    customers.name AS customer_name,
                    customers.company AS customer_company
                FROM estimates
                JOIN customers
                    ON customers.id = estimates.customer_id
                ORDER BY estimates.estimate_number DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]

    def delete(self, estimate_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM estimates WHERE id = ?",
                (estimate_id,),
            )

    @staticmethod
    def _insert_items(connection, estimate: Estimate) -> None:
        if estimate.id is None:
            raise ValueError("Estimate must have an ID before adding items.")

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
