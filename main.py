import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from database.database import initialize_database
from release_metadata import PRODUCT_NAME, PUBLISHER, VERSION
from services.application_paths import (
    get_application_paths,
    validate_application_data_directory,
)
from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(PRODUCT_NAME)
    app.setApplicationDisplayName(PRODUCT_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(PUBLISHER)

    paths = get_application_paths()
    try:
        initialize_database()
        validate_application_data_directory(paths)
    except Exception as error:
        QMessageBox.critical(
            None,
            f"{PRODUCT_NAME} Cannot Start",
            "Atlas could not initialize writable local data storage and will "
            "close safely. Check that this location is available and writable:\n\n"
            f"{paths.application_data_directory}\n\n"
            f"Details: {error}",
        )
        return 1

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
