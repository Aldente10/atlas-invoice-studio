from database.database import get_connection
from models.company_settings import CompanySettings


class SettingsRepository:
    def get(self) -> CompanySettings:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT business_name, contact_name, street_address,
                       city_state_zip, phone, email, website, license_number,
                       logo_path, default_estimate_notes, default_invoice_notes,
                       estimate_expiration_days, next_estimate_number,
                       next_invoice_number
                FROM company_settings
                WHERE id = 1
                """
            ).fetchone()
        return CompanySettings(**dict(row)) if row else CompanySettings()

    def save(self, settings: CompanySettings) -> None:
        if not settings.business_name.strip():
            raise ValueError("Business name is required.")
        if settings.estimate_expiration_days < 0:
            raise ValueError("Estimate expiration days cannot be negative.")
        if settings.next_estimate_number < 1 or settings.next_invoice_number < 1:
            raise ValueError("Next document numbers must be at least 1.")

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO company_settings (
                    id, business_name, contact_name, street_address,
                    city_state_zip, phone, email, website, license_number,
                    logo_path, default_estimate_notes, default_invoice_notes,
                    estimate_expiration_days, next_estimate_number,
                    next_invoice_number
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    business_name = excluded.business_name,
                    contact_name = excluded.contact_name,
                    street_address = excluded.street_address,
                    city_state_zip = excluded.city_state_zip,
                    phone = excluded.phone,
                    email = excluded.email,
                    website = excluded.website,
                    license_number = excluded.license_number,
                    logo_path = excluded.logo_path,
                    default_estimate_notes = excluded.default_estimate_notes,
                    default_invoice_notes = excluded.default_invoice_notes,
                    estimate_expiration_days = excluded.estimate_expiration_days,
                    next_estimate_number = excluded.next_estimate_number,
                    next_invoice_number = excluded.next_invoice_number,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    settings.business_name.strip(),
                    settings.contact_name.strip(),
                    settings.street_address.strip(),
                    settings.city_state_zip.strip(),
                    settings.phone.strip(),
                    settings.email.strip(),
                    settings.website.strip(),
                    settings.license_number.strip(),
                    settings.logo_path.strip(),
                    settings.default_estimate_notes.strip(),
                    settings.default_invoice_notes.strip(),
                    settings.estimate_expiration_days,
                    settings.next_estimate_number,
                    settings.next_invoice_number,
                ),
            )
