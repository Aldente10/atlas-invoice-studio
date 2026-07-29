from models.customer import Customer

from database.database import get_connection


class CustomerRepository:
    def create(self, customer: Customer) -> Customer:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO customers (
                    name,
                    company,
                    phone,
                    email,
                    billing_address,
                    job_address,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer.name.strip(),
                    customer.company.strip(),
                    customer.phone.strip(),
                    customer.email.strip(),
                    customer.billing_address.strip(),
                    customer.job_address.strip(),
                    customer.notes.strip(),
                ),
            )

            customer.id = cursor.lastrowid
            return customer

    def update(self, customer: Customer) -> None:
        if customer.id is None:
            raise ValueError("Cannot update a customer without an ID.")

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE customers
                SET
                    name = ?,
                    company = ?,
                    phone = ?,
                    email = ?,
                    billing_address = ?,
                    job_address = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    customer.name.strip(),
                    customer.company.strip(),
                    customer.phone.strip(),
                    customer.email.strip(),
                    customer.billing_address.strip(),
                    customer.job_address.strip(),
                    customer.notes.strip(),
                    customer.id,
                ),
            )

    def delete(self, customer_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM customers WHERE id = ?",
                (customer_id,),
            )

    def get_by_id(self, customer_id: int) -> Customer | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    company,
                    phone,
                    email,
                    billing_address,
                    job_address,
                    notes
                FROM customers
                WHERE id = ?
                """,
                (customer_id,),
            ).fetchone()

        return self._row_to_customer(row) if row else None

    def get_all(self) -> list[Customer]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    company,
                    phone,
                    email,
                    billing_address,
                    job_address,
                    notes
                FROM customers
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

        return [self._row_to_customer(row) for row in rows]

    def search(self, query: str) -> list[Customer]:
        search_term = f"%{query.strip()}%"

        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    company,
                    phone,
                    email,
                    billing_address,
                    job_address,
                    notes
                FROM customers
                WHERE
                    name LIKE ? COLLATE NOCASE
                    OR company LIKE ? COLLATE NOCASE
                    OR phone LIKE ?
                    OR email LIKE ? COLLATE NOCASE
                    OR job_address LIKE ? COLLATE NOCASE
                ORDER BY name COLLATE NOCASE
                """,
                (
                    search_term,
                    search_term,
                    search_term,
                    search_term,
                    search_term,
                ),
            ).fetchall()

        return [self._row_to_customer(row) for row in rows]

    @staticmethod
    def _row_to_customer(row) -> Customer:
        return Customer(
            id=row["id"],
            name=row["name"],
            company=row["company"],
            phone=row["phone"],
            email=row["email"],
            billing_address=row["billing_address"],
            job_address=row["job_address"],
            notes=row["notes"],
        )
