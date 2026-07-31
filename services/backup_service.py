from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import zipfile

from release_metadata import PRODUCT_NAME

from models.company_settings import CompanySettings
from services.application_paths import (
    ApplicationPaths,
    ensure_application_directories,
    get_application_paths,
)


BACKUP_FORMAT_VERSION = 1
DATABASE_MEMBER = "atlas_invoice_studio.db"
SETTINGS_MEMBER = "company_settings.json"
MANIFEST_MEMBER = "manifest.json"


class BackupValidationError(ValueError):
    """Raised when an archive is not a valid Atlas backup."""


@dataclass(frozen=True, slots=True)
class BackupContents:
    archive_path: Path
    created_at: str
    logo_member: str | None


class BackupService:
    def __init__(self, paths: ApplicationPaths | None = None) -> None:
        self.paths = paths or get_application_paths()

    def create_backup(
        self,
        destination: Path | None = None,
        *,
        reason: str = "manual",
    ) -> Path:
        ensure_application_directories(self.paths)
        if not self.paths.database_path.is_file():
            raise FileNotFoundError("The application database does not exist.")

        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"Atlas_Invoice_Studio_{reason}_{timestamp}.zip"
        if destination is None:
            archive_path = self.paths.backups_directory / filename
        else:
            destination = Path(destination)
            if destination.suffix.lower() == ".zip":
                archive_path = destination.with_name(
                    f"{destination.stem}_{timestamp}.zip"
                )
            else:
                archive_path = destination / filename
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory() as temporary_directory:
            database_copy = Path(temporary_directory) / DATABASE_MEMBER
            self._copy_database(database_copy)
            settings = self._read_settings(database_copy)
            logo_path = Path(settings.logo_path) if settings.logo_path else None
            logo_member = None
            if logo_path is not None and logo_path.is_file():
                logo_member = f"managed_logo{logo_path.suffix.lower()}"

            manifest = {
                "application": PRODUCT_NAME,
                "format_version": BACKUP_FORMAT_VERSION,
                "created_at": datetime.now().astimezone().isoformat(),
                "reason": reason,
                "database": DATABASE_MEMBER,
                "settings": SETTINGS_MEMBER,
                "managed_logo": logo_member,
                "generated_documents_included": False,
            }

            temporary_archive = archive_path.with_suffix(".zip.creating")
            if temporary_archive.exists():
                temporary_archive.unlink()
            try:
                with zipfile.ZipFile(
                    temporary_archive, "w", compression=zipfile.ZIP_DEFLATED
                ) as archive:
                    archive.write(database_copy, DATABASE_MEMBER)
                    archive.writestr(
                        SETTINGS_MEMBER,
                        json.dumps(settings.to_dict(), indent=2, sort_keys=True),
                    )
                    if logo_member and logo_path:
                        archive.write(logo_path, logo_member)
                    archive.writestr(
                        MANIFEST_MEMBER,
                        json.dumps(manifest, indent=2, sort_keys=True),
                    )
                temporary_archive.replace(archive_path)
            except Exception:
                if temporary_archive.exists():
                    temporary_archive.unlink()
                raise

        return archive_path

    def validate_backup(self, archive_path: Path) -> BackupContents:
        archive_path = Path(archive_path)
        if not archive_path.is_file() or not zipfile.is_zipfile(archive_path):
            raise BackupValidationError("The selected file is not a valid ZIP archive.")

        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                names = set(archive.namelist())
                if MANIFEST_MEMBER not in names:
                    raise BackupValidationError("The backup manifest is missing.")
                manifest = json.loads(archive.read(MANIFEST_MEMBER))
                if manifest.get("application") != PRODUCT_NAME:
                    raise BackupValidationError(f"This is not a {PRODUCT_NAME} backup.")
                if manifest.get("format_version") != BACKUP_FORMAT_VERSION:
                    raise BackupValidationError("This backup version is not supported.")
                if DATABASE_MEMBER not in names or SETTINGS_MEMBER not in names:
                    raise BackupValidationError("The backup is missing required data.")
                json.loads(archive.read(SETTINGS_MEMBER))

                logo_member = manifest.get("managed_logo")
                if logo_member and logo_member not in names:
                    raise BackupValidationError("The managed logo is missing.")

                with TemporaryDirectory() as temporary_directory:
                    database_copy = Path(temporary_directory) / DATABASE_MEMBER
                    with archive.open(DATABASE_MEMBER) as source, database_copy.open(
                        "wb"
                    ) as target:
                        shutil.copyfileobj(source, target)
                    self._validate_database(database_copy)
        except BackupValidationError:
            raise
        except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
            raise BackupValidationError(f"The backup is damaged: {error}") from error

        return BackupContents(
            archive_path=archive_path,
            created_at=str(manifest.get("created_at", "")),
            logo_member=logo_member,
        )

    def restore_backup(self, archive_path: Path) -> Path:
        contents = self.validate_backup(archive_path)
        ensure_application_directories(self.paths)
        safety_backup = self.create_backup(reason="pre_restore")

        with TemporaryDirectory() as temporary_directory:
            temporary_directory_path = Path(temporary_directory)
            staged_database = temporary_directory_path / DATABASE_MEMBER
            restored_logo_path: Path | None = None

            with zipfile.ZipFile(contents.archive_path, "r") as archive:
                with archive.open(DATABASE_MEMBER) as source, staged_database.open(
                    "wb"
                ) as target:
                    shutil.copyfileobj(source, target)

                if contents.logo_member:
                    suffix = Path(contents.logo_member).suffix.lower()
                    logo_name = datetime.now().strftime(
                        f"company_logo_restored_%Y%m%d_%H%M%S_%f{suffix}"
                    )
                    restored_logo_path = self.paths.managed_assets_directory / logo_name
                    staged_logo = temporary_directory_path / logo_name
                    with archive.open(contents.logo_member) as source, staged_logo.open(
                        "wb"
                    ) as target:
                        shutil.copyfileobj(source, target)
                    shutil.copy2(staged_logo, restored_logo_path)

            with closing(sqlite3.connect(staged_database)) as connection:
                connection.execute(
                    "UPDATE company_settings SET logo_path = ? WHERE id = 1",
                    (str(restored_logo_path) if restored_logo_path else "",),
                )
                connection.commit()

            self._validate_database(staged_database)

            replacement = self.paths.database_path.with_suffix(".db.restore-staging")
            if replacement.exists():
                replacement.unlink()
            try:
                shutil.copy2(staged_database, replacement)
                replacement.replace(self.paths.database_path)
            except Exception:
                if replacement.exists():
                    replacement.unlink()
                raise

        return safety_backup

    def _copy_database(self, destination: Path) -> None:
        with closing(sqlite3.connect(self.paths.database_path)) as source:
            with closing(sqlite3.connect(destination)) as target:
                source.backup(target)

    @staticmethod
    def _read_settings(database_path: Path) -> CompanySettings:
        with closing(sqlite3.connect(database_path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT business_name, contact_name, street_address,
                       city_state_zip, phone, email, website, license_number,
                       logo_path, default_estimate_notes, default_invoice_notes,
                       estimate_expiration_days, next_estimate_number,
                       next_invoice_number
                FROM company_settings WHERE id = 1
                """
            ).fetchone()

        return CompanySettings(**dict(row)) if row else CompanySettings()

    @staticmethod
    def _validate_database(database_path: Path) -> None:
        required_tables = {
            "customers",
            "services",
            "estimates",
            "estimate_items",
            "invoices",
            "invoice_items",
            "company_settings",
        }
        try:
            with closing(
                sqlite3.connect(
                    f"file:{database_path}?mode=ro",
                    uri=True,
                )
            ) as connection:
                quick_check = connection.execute(
                    "PRAGMA quick_check"
                ).fetchone()[0]

                if quick_check != "ok":
                    raise BackupValidationError(
                        f"The backup database failed integrity checking: {quick_check}"
                    )

                rows = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
        except sqlite3.DatabaseError as error:
            raise BackupValidationError("The backup database cannot be opened.") from error

        tables = {row[0] for row in rows}
        missing = required_tables - tables
        if missing:
            raise BackupValidationError(
                "The backup database is missing required tables: "
                + ", ".join(sorted(missing))
            )
