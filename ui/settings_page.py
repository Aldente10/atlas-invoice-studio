from datetime import datetime
from pathlib import Path
import shutil

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.settings_repository import SettingsRepository
from database.estimate_repository import EstimateRepository
from database.invoice_repository import InvoiceRepository
from models.company_settings import CompanySettings
from release_metadata import PRODUCT_NAME
from services.application_paths import ensure_application_directories, get_application_paths
from services.backup_service import BackupService, BackupValidationError


class SettingsPage(QWidget):
    settings_saved = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboard")
        self.settings_repository = SettingsRepository()
        self.paths = get_application_paths()
        self.backup_service = BackupService(self.paths)
        self.selected_logo_path = ""
        self.build_ui()
        self.load_settings()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        heading = QLabel("Settings")
        heading.setObjectName("pageHeading")
        subtitle = QLabel(
            "Configure company details, document defaults, numbering, and local data protection."
        )
        subtitle.setObjectName("pageSubtitle")
        root.addWidget(heading)
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("settingsScroll")
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)

        company_panel = self._panel("Company Information")
        company_form = QFormLayout()
        company_form.setSpacing(12)
        self.business_name_input = self._line_input()
        self.contact_name_input = self._line_input()
        self.street_address_input = self._line_input()
        self.city_state_zip_input = self._line_input()
        self.phone_input = self._line_input()
        self.email_input = self._line_input()
        self.website_input = self._line_input()
        self.license_number_input = self._line_input()
        self._add_form_row(company_form, "Business Name *", self.business_name_input)
        self._add_form_row(company_form, "Owner / Contact", self.contact_name_input)
        self._add_form_row(company_form, "Street Address", self.street_address_input)
        self._add_form_row(company_form, "City / State / ZIP", self.city_state_zip_input)
        self._add_form_row(company_form, "Phone", self.phone_input)
        self._add_form_row(company_form, "Email", self.email_input)
        self._add_form_row(company_form, "Website", self.website_input)
        self._add_form_row(company_form, "License Number", self.license_number_input)
        company_panel.layout().addLayout(company_form)

        logo_row = QHBoxLayout()
        self.logo_preview = QLabel("No logo selected")
        self.logo_preview.setObjectName("logoPreview")
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setFixedSize(220, 100)
        choose_logo = QPushButton("Select Logo…")
        choose_logo.setObjectName("secondaryButton")
        choose_logo.clicked.connect(self.select_logo)
        logo_row.addWidget(self.logo_preview)
        logo_row.addWidget(choose_logo)
        logo_row.addStretch()
        company_panel.layout().addLayout(logo_row)

        defaults_panel = self._panel("Document Defaults")
        defaults_form = QFormLayout()
        defaults_form.setSpacing(12)
        self.estimate_notes_input = QTextEdit()
        self.estimate_notes_input.setObjectName("formInput")
        self.estimate_notes_input.setFixedHeight(80)
        self.invoice_notes_input = QTextEdit()
        self.invoice_notes_input.setObjectName("formInput")
        self.invoice_notes_input.setFixedHeight(80)
        self.expiration_days_input = QSpinBox()
        self.expiration_days_input.setObjectName("formInput")
        self.expiration_days_input.setRange(0, 3650)
        self.expiration_days_input.setSuffix(" days")
        self.next_estimate_input = QSpinBox()
        self.next_estimate_input.setObjectName("formInput")
        self.next_estimate_input.setRange(1, 999999)
        self.next_estimate_input.setToolTip(
            "Existing estimate numbers are never reused; this value acts as a minimum."
        )
        self.next_invoice_input = QSpinBox()
        self.next_invoice_input.setObjectName("formInput")
        self.next_invoice_input.setRange(1, 999999)
        self.next_invoice_input.setToolTip(
            "Existing invoice numbers are never reused; this value acts as a minimum."
        )
        self._add_form_row(defaults_form, "Default Estimate Notes / Terms", self.estimate_notes_input)
        self._add_form_row(defaults_form, "Default Invoice Notes / Terms", self.invoice_notes_input)
        self._add_form_row(defaults_form, "Estimate Expiration", self.expiration_days_input)
        self._add_form_row(defaults_form, "Next Estimate Number", self.next_estimate_input)
        self._add_form_row(defaults_form, "Next Invoice Number", self.next_invoice_input)
        defaults_panel.layout().addLayout(defaults_form)

        save_row = QHBoxLayout()
        save_button = QPushButton("Save Settings")
        save_button.setObjectName("primaryButton")
        save_button.setMinimumSize(150, 42)
        save_button.clicked.connect(self.save_settings)
        save_row.addStretch()
        save_row.addWidget(save_button)
        defaults_panel.layout().addLayout(save_row)

        data_panel = self._panel("Data Storage and Recovery")
        data_path = QLabel(
            f"Live application data: {self.paths.application_data_directory}"
        )
        data_path.setObjectName("pageSubtitle")
        data_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        explanation = QLabel(
            "Backups include the database, company settings, and managed logo. "
            "Generated PDFs are intentionally excluded."
        )
        explanation.setObjectName("pageSubtitle")
        explanation.setWordWrap(True)
        backup_row = QHBoxLayout()
        backup_button = QPushButton("Backup Data…")
        backup_button.setObjectName("secondaryButton")
        backup_button.clicked.connect(self.backup_data)
        restore_button = QPushButton("Restore Data…")
        restore_button.setObjectName("dangerButton")
        restore_button.clicked.connect(self.restore_data)
        backup_row.addWidget(backup_button)
        backup_row.addWidget(restore_button)
        backup_row.addStretch()
        data_panel.layout().addWidget(data_path)
        data_panel.layout().addWidget(explanation)
        data_panel.layout().addLayout(backup_row)

        content_layout.addWidget(company_panel)
        content_layout.addWidget(defaults_panel)
        content_layout.addWidget(data_panel)
        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    @staticmethod
    def _add_form_row(form, label_text: str, field) -> None:
        label = QLabel(label_text)
        label.setObjectName("settingsFormLabel")
        label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        form.addRow(label, field)

    @staticmethod
    def _line_input() -> QLineEdit:
        line_input = QLineEdit()
        line_input.setObjectName("formInput")
        return line_input

    @staticmethod
    def _panel(title: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 20)
        layout.setSpacing(14)
        label = QLabel(title)
        label.setObjectName("panelTitle")
        layout.addWidget(label)
        return panel

    def load_settings(self) -> None:
        settings = self.settings_repository.get()
        self.business_name_input.setText(settings.business_name)
        self.contact_name_input.setText(settings.contact_name)
        self.street_address_input.setText(settings.street_address)
        self.city_state_zip_input.setText(settings.city_state_zip)
        self.phone_input.setText(settings.phone)
        self.email_input.setText(settings.email)
        self.website_input.setText(settings.website)
        self.license_number_input.setText(settings.license_number)
        self.estimate_notes_input.setPlainText(settings.default_estimate_notes)
        self.invoice_notes_input.setPlainText(settings.default_invoice_notes)
        self.expiration_days_input.setValue(settings.estimate_expiration_days)
        self.next_estimate_input.setValue(EstimateRepository().next_estimate_number())
        self.next_invoice_input.setValue(InvoiceRepository().next_invoice_number())
        self.selected_logo_path = settings.logo_path
        self.update_logo_preview()

    def select_logo(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Company Logo",
            str(Path(self.selected_logo_path).parent) if self.selected_logo_path else "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)",
        )
        if filename:
            self.selected_logo_path = filename
            self.update_logo_preview()

    def update_logo_preview(self) -> None:
        logo_path = Path(self.selected_logo_path) if self.selected_logo_path else None
        if logo_path is None or not logo_path.is_file():
            self.logo_preview.setPixmap(QPixmap())
            self.logo_preview.setText("No logo selected")
            return
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            self.logo_preview.setPixmap(QPixmap())
            self.logo_preview.setText("Unable to preview logo")
            return
        self.logo_preview.setText("")
        self.logo_preview.setPixmap(
            pixmap.scaled(
                self.logo_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def save_settings(self) -> None:
        business_name = self.business_name_input.text().strip()
        if not business_name:
            QMessageBox.warning(
                self, "Business Name Required", "Enter a business name before saving."
            )
            self.business_name_input.setFocus()
            return

        try:
            managed_logo = self._manage_selected_logo()
            settings = CompanySettings(
                business_name=business_name,
                contact_name=self.contact_name_input.text().strip(),
                street_address=self.street_address_input.text().strip(),
                city_state_zip=self.city_state_zip_input.text().strip(),
                phone=self.phone_input.text().strip(),
                email=self.email_input.text().strip(),
                website=self.website_input.text().strip(),
                license_number=self.license_number_input.text().strip(),
                logo_path=managed_logo,
                default_estimate_notes=self.estimate_notes_input.toPlainText().strip(),
                default_invoice_notes=self.invoice_notes_input.toPlainText().strip(),
                estimate_expiration_days=self.expiration_days_input.value(),
                next_estimate_number=self.next_estimate_input.value(),
                next_invoice_number=self.next_invoice_input.value(),
            )
            self.settings_repository.save(settings)
        except Exception as error:
            QMessageBox.critical(self, "Unable to Save Settings", str(error))
            return

        self.selected_logo_path = managed_logo
        self.update_logo_preview()
        self.settings_saved.emit(settings.business_name)
        QMessageBox.information(
            self, "Settings Saved", "Company settings were saved successfully."
        )

    def _manage_selected_logo(self) -> str:
        if not self.selected_logo_path:
            return ""
        source = Path(self.selected_logo_path)
        if not source.is_file():
            raise ValueError("The selected logo file could not be found.")
        if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            raise ValueError("Choose a PNG, JPG, JPEG, or BMP logo.")

        ensure_application_directories(self.paths)
        try:
            source.relative_to(self.paths.managed_assets_directory)
            return str(source)
        except ValueError:
            pass

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        target = self.paths.managed_assets_directory / (
            f"company_logo_{timestamp}{source.suffix.lower()}"
        )
        shutil.copy2(source, target)
        return str(target)

    def backup_data(self) -> None:
        ensure_application_directories(self.paths)
        destination = QFileDialog.getExistingDirectory(
            self,
            "Choose Backup Destination",
            str(self.paths.backups_directory),
        )
        if not destination:
            return
        try:
            archive_path = self.backup_service.create_backup(Path(destination))
        except Exception as error:
            QMessageBox.critical(self, "Unable to Create Backup", str(error))
            return
        QMessageBox.information(
            self, "Backup Created", f"Your data backup was created here:\n{archive_path}"
        )

    def restore_data(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {PRODUCT_NAME} Backup",
            str(self.paths.backups_directory),
            "Atlas Backup (*.zip)",
        )
        if not filename:
            return
        try:
            details = self.backup_service.validate_backup(Path(filename))
        except BackupValidationError as error:
            QMessageBox.critical(self, "Invalid Backup", str(error))
            return

        answer = QMessageBox.warning(
            self,
            "Restore Application Data",
            "This will replace all current customers, services, estimates, "
            "invoices, and settings with the selected backup. A safety backup "
            f"will be created first.\n\nBackup created: {details.created_at}\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            safety_backup = self.backup_service.restore_backup(Path(filename))
        except Exception as error:
            QMessageBox.critical(self, "Unable to Restore Backup", str(error))
            return
        QMessageBox.information(
            self,
            "Restore Complete",
            f"The backup was restored successfully. Restart {PRODUCT_NAME} "
            "before continuing.\n\nA safety backup of the previous data is here:\n"
            f"{safety_backup}",
        )
