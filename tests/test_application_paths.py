from pathlib import Path

from services.application_paths import (
    DATA_DIRECTORY_ENVIRONMENT_VARIABLE,
    migrate_legacy_database_if_needed,
    resolve_application_paths,
)


def test_packaged_windows_paths_use_local_app_data(tmp_path) -> None:
    local_app_data = tmp_path / "LocalAppData"
    paths = resolve_application_paths(
        packaged=True,
        platform_name="win32",
        environment={"LOCALAPPDATA": str(local_app_data)},
        home_directory=tmp_path / "Home",
        project_root=tmp_path / "Project",
    )

    expected_root = local_app_data / "Atlas Invoice Studio"
    assert paths.application_data_directory == expected_root
    assert paths.database_path == expected_root / "atlas_invoice_studio.db"
    assert paths.generated_documents_directory == expected_root / "generated_documents"
    assert paths.backups_directory == expected_root / "backups"
    assert paths.managed_assets_directory == expected_root / "managed_assets"


def test_development_paths_preserve_repository_data_layout(tmp_path) -> None:
    paths = resolve_application_paths(
        packaged=False,
        environment={},
        project_root=tmp_path,
    )

    assert paths.application_data_directory == tmp_path
    assert paths.database_path == tmp_path / "data" / "atlas_invoice_studio.db"


def test_environment_override_is_available_for_testing_and_support(tmp_path) -> None:
    override = tmp_path / "isolated-data"
    paths = resolve_application_paths(
        packaged=True,
        platform_name="win32",
        environment={DATA_DIRECTORY_ENVIRONMENT_VARIABLE: str(override)},
        project_root=tmp_path / "Project",
    )

    assert paths.application_data_directory == override
    assert paths.database_path == override / "atlas_invoice_studio.db"


def test_legacy_migration_copies_once_without_overwriting(tmp_path) -> None:
    project_root = tmp_path / "Project"
    legacy = project_root / "data" / "atlas_invoice_studio.db"
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"legacy")
    paths = resolve_application_paths(
        packaged=True,
        platform_name="win32",
        environment={"LOCALAPPDATA": str(tmp_path / "Local")},
        project_root=project_root,
    )

    assert migrate_legacy_database_if_needed(paths) is True
    assert paths.database_path.read_bytes() == b"legacy"

    paths.database_path.write_bytes(b"live")
    assert migrate_legacy_database_if_needed(paths) is False
    assert paths.database_path.read_bytes() == b"live"
