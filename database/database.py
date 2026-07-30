import sqlite3
from pathlib import Path

from services.application_paths import (
    ensure_application_directories,
    get_application_paths,
    migrate_legacy_database_if_needed,
)


# Optional override retained for isolated tests and embedding scenarios.
DATABASE_PATH = None


def get_database_path() -> Path:
    return DATABASE_PATH or get_application_paths().database_path


def get_connection() -> sqlite3.Connection:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database() -> None:
    if DATABASE_PATH is None:
        paths = get_application_paths()
        ensure_application_directories(paths)
        migrate_legacy_database_if_needed(paths)

    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                billing_address TEXT NOT NULL DEFAULT '',
                job_address TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_customers_name
            ON customers(name);

            CREATE INDEX IF NOT EXISTS idx_customers_company
            ON customers(company);

            CREATE TABLE IF NOT EXISTS estimates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimate_number INTEGER NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                estimate_date TEXT NOT NULL,
                expiration_date TEXT NOT NULL,
                job_address TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                subtotal_cents INTEGER NOT NULL DEFAULT 0,
                tax_rate REAL NOT NULL DEFAULT 0,
                tax_cents INTEGER NOT NULL DEFAULT 0,
                total_cents INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Draft',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
                    ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS estimate_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estimate_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1,
                rate_cents INTEGER NOT NULL DEFAULT 0,
                amount_cents INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (estimate_id)
                    REFERENCES estimates(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_estimates_customer
            ON estimates(customer_id);

            CREATE INDEX IF NOT EXISTS idx_estimates_number
            ON estimates(estimate_number);

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number INTEGER NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                source_estimate_id INTEGER,
                invoice_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                job_address TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                subtotal_cents INTEGER NOT NULL DEFAULT 0,
                tax_rate REAL NOT NULL DEFAULT 0,
                tax_cents INTEGER NOT NULL DEFAULT 0,
                total_cents INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Draft',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id)
                    REFERENCES customers(id)
                    ON DELETE RESTRICT,
                FOREIGN KEY (source_estimate_id)
                    REFERENCES estimates(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1,
                rate_cents INTEGER NOT NULL DEFAULT 0,
                amount_cents INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (invoice_id)
                    REFERENCES invoices(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_invoices_customer
            ON invoices(customer_id);

            CREATE INDEX IF NOT EXISTS idx_invoices_number
            ON invoices(invoice_number);

            CREATE INDEX IF NOT EXISTS idx_invoices_source_estimate
            ON invoices(source_estimate_id);

            CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice
            ON invoice_items(invoice_id);

            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                business_name TEXT NOT NULL DEFAULT '',
                contact_name TEXT NOT NULL DEFAULT '',
                street_address TEXT NOT NULL DEFAULT '',
                city_state_zip TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                license_number TEXT NOT NULL DEFAULT '',
                logo_path TEXT NOT NULL DEFAULT '',
                default_estimate_notes TEXT NOT NULL DEFAULT
                    'Materials and labor included.',
                default_invoice_notes TEXT NOT NULL DEFAULT
                    'Thank you for your business.',
                estimate_expiration_days INTEGER NOT NULL DEFAULT 14,
                next_estimate_number INTEGER NOT NULL DEFAULT 1039,
                next_invoice_number INTEGER NOT NULL DEFAULT 1001,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                default_quantity REAL NOT NULL DEFAULT 1,
                default_rate_cents INTEGER NOT NULL DEFAULT 0,
                taxable INTEGER NOT NULL DEFAULT 0,
                favorite INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_services_name
            ON services(name);

            CREATE INDEX IF NOT EXISTS idx_services_category
            ON services(category);
            """
        )
