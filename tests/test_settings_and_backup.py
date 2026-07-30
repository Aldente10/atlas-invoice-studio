import json
import zipfile

import pytest

from database import database
from database.customer_repository import CustomerRepository
from database.estimate_repository import EstimateRepository
from database.invoice_repository import InvoiceRepository
from database.settings_repository import SettingsRepository
from models.company_settings import CompanySettings
from models.customer import Customer
from pdf.estimate_pdf import company_pdf_data
from services.application_paths import ApplicationPaths
from services.backup_service import (
    BackupService,
    BackupValidationError,
    MANIFEST_MEMBER,
    SETTINGS_MEMBER,
)


@pytest.fixture
def isolated_application(tmp_path, monkeypatch):
    database_path = tmp_path / "atlas_invoice_studio.db"
    monkeypatch.setattr(database, "DATABASE_PATH", database_path)
    paths = ApplicationPaths(
        application_data_directory=tmp_path,
        database_path=database_path,
        generated_documents_directory=tmp_path / "generated_documents",
        backups_directory=tmp_path / "backups",
        managed_assets_directory=tmp_path / "managed_assets",
        legacy_database_path=tmp_path / "legacy.db",
    )
    database.initialize_database()
    return paths


def test_default_settings_are_safe_and_use_existing_document_defaults(
    isolated_application,
) -> None:
    settings = SettingsRepository().get()

    assert settings.business_name == ""
    assert settings.default_estimate_notes == "Materials and labor included."
    assert settings.default_invoice_notes == "Thank you for your business."
    assert settings.estimate_expiration_days == 14
    assert settings.next_estimate_number == 1039
    assert settings.next_invoice_number == 1001


def test_settings_persist_and_adapt_to_pdf_company_data(isolated_application) -> None:
    repository = SettingsRepository()
    expected = CompanySettings(
        business_name="Danny's Painting",
        contact_name="Danny",
        street_address="10 Brush Lane",
        city_state_zip="Palm Coast, FL 32137",
        phone="555-0100",
        email="danny@example.com",
        website="danny-paints.example",
        license_number="LIC-42",
        default_estimate_notes="Paint and standard prep included.",
        default_invoice_notes="Payment due within 30 days.",
        estimate_expiration_days=21,
        next_estimate_number=2200,
        next_invoice_number=3100,
    )

    repository.save(expected)
    loaded = repository.get()
    pdf_data = company_pdf_data(loaded)

    assert loaded == expected
    assert EstimateRepository().next_estimate_number() == 2200
    assert InvoiceRepository().next_invoice_number() == 3100
    assert pdf_data["name"] == "Danny's Painting"
    assert pdf_data["contact_name"] == "Danny"
    assert pdf_data["address"] == "10 Brush Lane<br/>Palm Coast, FL 32137"
    assert pdf_data["license_number"] == "LIC-42"


def test_settings_reject_empty_business_name(isolated_application) -> None:
    with pytest.raises(ValueError, match="Business name"):
        SettingsRepository().save(CompanySettings())


def test_backup_contains_valid_database_settings_and_logo(isolated_application) -> None:
    paths = isolated_application
    paths.managed_assets_directory.mkdir()
    logo_path = paths.managed_assets_directory / "company_logo.png"
    logo_path.write_bytes(b"test-logo")
    SettingsRepository().save(
        CompanySettings(business_name="Danny's Painting", logo_path=str(logo_path))
    )
    service = BackupService(paths)

    archive_path = service.create_backup()
    details = service.validate_backup(archive_path)

    assert archive_path.parent == paths.backups_directory
    assert details.logo_member == "managed_logo.png"
    with zipfile.ZipFile(archive_path) as archive:
        settings = json.loads(archive.read(SETTINGS_MEMBER))
        assert settings["business_name"] == "Danny's Painting"
        assert "generated_documents" not in archive.namelist()


def test_restore_validates_then_creates_safety_backup_and_replaces_data(
    isolated_application,
) -> None:
    paths = isolated_application
    settings_repository = SettingsRepository()
    customers = CustomerRepository()
    settings_repository.save(CompanySettings(business_name="Backup Company"))
    customers.create(Customer(name="Customer From Backup"))
    service = BackupService(paths)
    archive_path = service.create_backup()

    settings_repository.save(CompanySettings(business_name="Current Company"))
    customers.create(Customer(name="Current Customer"))
    safety_backup = service.restore_backup(archive_path)

    assert safety_backup.is_file()
    assert "pre_restore" in safety_backup.name
    assert SettingsRepository().get().business_name == "Backup Company"
    assert [customer.name for customer in CustomerRepository().get_all()] == [
        "Customer From Backup"
    ]
    service.validate_backup(safety_backup)


def test_invalid_backup_is_rejected_without_replacing_live_data(
    isolated_application,
) -> None:
    paths = isolated_application
    SettingsRepository().save(CompanySettings(business_name="Live Company"))
    invalid_archive = paths.application_data_directory / "invalid.zip"
    with zipfile.ZipFile(invalid_archive, "w") as archive:
        archive.writestr(
            MANIFEST_MEMBER,
            json.dumps(
                {
                    "application": "Atlas Invoice Studio",
                    "format_version": 1,
                }
            ),
        )

    with pytest.raises(BackupValidationError):
        BackupService(paths).restore_backup(invalid_archive)

    assert SettingsRepository().get().business_name == "Live Company"
    assert not paths.backups_directory.exists()
