from database.database import get_connection
from models.service import Service


class ServiceRepository:
    def create(self, service: Service) -> Service:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO services (
                    name,
                    category,
                    description,
                    default_quantity,
                    default_rate_cents,
                    taxable,
                    favorite,
                    active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    service.name.strip(),
                    service.category.strip(),
                    service.description.strip(),
                    service.default_quantity,
                    service.default_rate_cents,
                    int(service.taxable),
                    int(service.favorite),
                    int(service.active),
                ),
            )

            service.id = cursor.lastrowid

        return service

    def update(self, service: Service) -> None:
        if service.id is None:
            raise ValueError("Cannot update a service without an ID.")

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE services
                SET
                    name = ?,
                    category = ?,
                    description = ?,
                    default_quantity = ?,
                    default_rate_cents = ?,
                    taxable = ?,
                    favorite = ?,
                    active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    service.name.strip(),
                    service.category.strip(),
                    service.description.strip(),
                    service.default_quantity,
                    service.default_rate_cents,
                    int(service.taxable),
                    int(service.favorite),
                    int(service.active),
                    service.id,
                ),
            )

    def delete(self, service_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM services WHERE id = ?",
                (service_id,),
            )

    def get_by_id(self, service_id: int) -> Service | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    category,
                    description,
                    default_quantity,
                    default_rate_cents,
                    taxable,
                    favorite,
                    active
                FROM services
                WHERE id = ?
                """,
                (service_id,),
            ).fetchone()

        return self._row_to_service(row) if row else None

    def get_all(self, active_only: bool = False) -> list[Service]:
        query = """
            SELECT
                id,
                name,
                category,
                description,
                default_quantity,
                default_rate_cents,
                taxable,
                favorite,
                active
            FROM services
        """

        parameters: tuple = ()

        if active_only:
            query += " WHERE active = ?"
            parameters = (1,)

        query += """
            ORDER BY
                favorite DESC,
                category COLLATE NOCASE,
                name COLLATE NOCASE
        """

        with get_connection() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._row_to_service(row) for row in rows]

    def search(
        self,
        search_text: str,
        category: str = "",
        favorites_only: bool = False,
        active_only: bool = False,
    ) -> list[Service]:
        clauses: list[str] = []
        parameters: list[object] = []

        if search_text.strip():
            search_term = f"%{search_text.strip()}%"
            clauses.append(
                """
                (
                    name LIKE ? COLLATE NOCASE
                    OR category LIKE ? COLLATE NOCASE
                    OR description LIKE ? COLLATE NOCASE
                )
                """
            )
            parameters.extend(
                [search_term, search_term, search_term]
            )

        if category.strip():
            clauses.append("category = ? COLLATE NOCASE")
            parameters.append(category.strip())

        if favorites_only:
            clauses.append("favorite = 1")

        if active_only:
            clauses.append("active = 1")

        query = """
            SELECT
                id,
                name,
                category,
                description,
                default_quantity,
                default_rate_cents,
                taxable,
                favorite,
                active
            FROM services
        """

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += """
            ORDER BY
                favorite DESC,
                category COLLATE NOCASE,
                name COLLATE NOCASE
        """

        with get_connection() as connection:
            rows = connection.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return [self._row_to_service(row) for row in rows]

    def get_categories(self) -> list[str]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT category
                FROM services
                WHERE TRIM(category) <> ''
                ORDER BY category COLLATE NOCASE
                """
            ).fetchall()

        return [row["category"] for row in rows]

    @staticmethod
    def _row_to_service(row) -> Service:
        return Service(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            description=row["description"],
            default_quantity=row["default_quantity"],
            default_rate_cents=row["default_rate_cents"],
            taxable=bool(row["taxable"]),
            favorite=bool(row["favorite"]),
            active=bool(row["active"]),
        )
