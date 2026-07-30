from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import sys


APPLICATION_DIRECTORY_NAME = "Atlas Invoice Studio"
DATA_DIRECTORY_ENVIRONMENT_VARIABLE = "ATLAS_INVOICE_STUDIO_DATA_DIR"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    application_data_directory: Path
    database_path: Path
    generated_documents_directory: Path
    backups_directory: Path
    managed_assets_directory: Path
    legacy_database_path: Path


def resolve_application_paths(
    *,
    packaged: bool | None = None,
    platform_name: str | None = None,
    environment: dict[str, str] | None = None,
    home_directory: Path | None = None,
    project_root: Path | None = None,
) -> ApplicationPaths:
    """Resolve writable paths without creating or changing anything."""
    environment = environment if environment is not None else os.environ
    platform_name = platform_name or sys.platform
    packaged = getattr(sys, "frozen", False) if packaged is None else packaged
    home_directory = home_directory or Path.home()
    project_root = project_root or PROJECT_ROOT
    override = environment.get(DATA_DIRECTORY_ENVIRONMENT_VARIABLE)

    if override:
        data_directory = Path(override).expanduser()
        database_path = data_directory / "atlas_invoice_studio.db"
    elif packaged:
        if platform_name.startswith("win"):
            local_app_data = environment.get("LOCALAPPDATA")
            base = (
                Path(local_app_data)
                if local_app_data
                else home_directory / "AppData" / "Local"
            )
        else:
            xdg_data_home = environment.get("XDG_DATA_HOME")
            base = (
                Path(xdg_data_home)
                if xdg_data_home
                else home_directory / ".local" / "share"
            )
        data_directory = base / APPLICATION_DIRECTORY_NAME
        database_path = data_directory / "atlas_invoice_studio.db"
    else:
        # Keep repository-local paths in source checkouts for convenient
        # development and compatibility with existing beta data.
        data_directory = project_root
        database_path = project_root / "data" / "atlas_invoice_studio.db"

    return ApplicationPaths(
        application_data_directory=data_directory,
        database_path=database_path,
        generated_documents_directory=data_directory / "generated_documents",
        backups_directory=data_directory / "backups",
        managed_assets_directory=data_directory / "managed_assets",
        legacy_database_path=project_root / "data" / "atlas_invoice_studio.db",
    )


def get_application_paths() -> ApplicationPaths:
    return resolve_application_paths()


def ensure_application_directories(paths: ApplicationPaths | None = None) -> None:
    paths = paths or get_application_paths()
    paths.database_path.parent.mkdir(parents=True, exist_ok=True)
    paths.generated_documents_directory.mkdir(parents=True, exist_ok=True)
    paths.backups_directory.mkdir(parents=True, exist_ok=True)
    paths.managed_assets_directory.mkdir(parents=True, exist_ok=True)


def migrate_legacy_database_if_needed(
    paths: ApplicationPaths | None = None,
) -> bool:
    """Copy legacy development data once; never overwrite either database."""
    paths = paths or get_application_paths()
    target = paths.database_path
    legacy = paths.legacy_database_path

    if target == legacy or target.exists() or not legacy.is_file():
        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_target = target.with_suffix(target.suffix + ".migrating")
    if temporary_target.exists():
        temporary_target.unlink()

    try:
        shutil.copy2(legacy, temporary_target)
        temporary_target.replace(target)
    except Exception:
        if temporary_target.exists():
            temporary_target.unlink()
        raise
    return True
