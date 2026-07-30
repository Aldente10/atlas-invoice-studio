from datetime import date, timedelta

from PySide6.QtCore import QDate, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.customer_repository import CustomerRepository
from database.estimate_repository import EstimateRepository
from database.invoice_repository import (
    DuplicateEstimateConversionError,
    InvoiceRepository,
)
from database.settings_repository import SettingsRepository
from models.estimate import Estimate, EstimateItem
from pdf.estimate_pdf import generate_estimate_pdf
from services.estimate_items import estimate_item_from_service
from ui.customer_dialog import CustomerDialog
from ui.service_selection_dialog import ServiceSelectionDialog


class EstimatesPage(QWidget):
    invoice_created = Signal(int)

    DESCRIPTION_COLUMN = 0
    QUANTITY_COLUMN = 1
    RATE_COLUMN = 2
    AMOUNT_COLUMN = 3

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboard")

        self.customer_repository = CustomerRepository()
        self.estimate_repository = EstimateRepository()
        self.invoice_repository = InvoiceRepository()
        self.settings_repository = SettingsRepository()

        self.current_estimate_id: int | None = None

        self.build_ui()
        self.load_customers()
        self.load_saved_estimates()
        self.start_new_estimate()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()

        heading_group = QVBoxLayout()
        heading_group.setSpacing(2)

        heading = QLabel("Estimates")
        heading.setObjectName("pageHeading")

        subtitle = QLabel(
            "Create professional estimates with automatic totals and numbering."
        )
        subtitle.setObjectName("pageSubtitle")

        heading_group.addWidget(heading)
        heading_group.addWidget(subtitle)

        new_button = QPushButton("+ New Estimate")
        new_button.setObjectName("primaryButton")
        new_button.setFixedSize(145, 42)
        new_button.clicked.connect(self.start_new_estimate)

        header.addLayout(heading_group)
        header.addStretch()
        header.addWidget(new_button)

        root.addLayout(header)

        saved_row = QHBoxLayout()

        saved_label = QLabel("Open Saved Estimate")
        saved_label.setObjectName("metricTitle")

        self.saved_estimates_combo = QComboBox()
        self.saved_estimates_combo.setObjectName("formInput")
        self.saved_estimates_combo.setMinimumWidth(360)

        open_button = QPushButton("Open")
        open_button.setObjectName("secondaryButton")
        open_button.clicked.connect(self.open_saved_estimate)

        delete_estimate_button = QPushButton("Delete Estimate")
        delete_estimate_button.setObjectName("dangerButton")
        delete_estimate_button.clicked.connect(self.delete_current_estimate)

        convert_button = QPushButton("Convert to Invoice")
        convert_button.setObjectName("primaryButton")
        convert_button.clicked.connect(self.convert_to_invoice)

        saved_row.addWidget(saved_label)
        saved_row.addWidget(self.saved_estimates_combo)
        saved_row.addWidget(open_button)
        saved_row.addWidget(delete_estimate_button)
        saved_row.addWidget(convert_button)
        saved_row.addStretch()

        root.addLayout(saved_row)

        editor = QFrame()
        editor.setObjectName("panel")

        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(22, 18, 22, 20)
        editor_layout.setSpacing(16)

        editor_layout.addLayout(self.build_document_header())
        editor_layout.addWidget(self.build_items_table(), 1)
        editor_layout.addLayout(self.build_item_buttons())
        editor_layout.addLayout(self.build_bottom_section())

        root.addWidget(editor, 1)

    def build_document_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.number_input = QSpinBox()
        self.number_input.setRange(1, 999999)
        self.number_input.setObjectName("formInput")
        self.number_input.setPrefix("Estimate #")

        customer_widget = QWidget()
        customer_layout = QHBoxLayout(customer_widget)
        customer_layout.setContentsMargins(0, 0, 0, 0)
        customer_layout.setSpacing(6)

        self.customer_combo = QComboBox()
        self.customer_combo.setObjectName("formInput")
        self.customer_combo.setMinimumWidth(240)
        self.customer_combo.currentIndexChanged.connect(
            self.customer_changed
        )

        add_customer_button = QPushButton("+ Customer")
        add_customer_button.setObjectName("secondaryButton")
        add_customer_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_customer_button.clicked.connect(self.create_customer)

        customer_layout.addWidget(self.customer_combo, 1)
        customer_layout.addWidget(add_customer_button)

        self.estimate_date_input = QDateEdit()
        self.estimate_date_input.setObjectName("formInput")
        self.estimate_date_input.setCalendarPopup(True)
        self.estimate_date_input.setDisplayFormat("MM/dd/yyyy")

        self.expiration_date_input = QDateEdit()
        self.expiration_date_input.setObjectName("formInput")
        self.expiration_date_input.setCalendarPopup(True)
        self.expiration_date_input.setDisplayFormat("MM/dd/yyyy")

        layout.addWidget(self.number_input)
        layout.addWidget(customer_widget, 1)
        layout.addWidget(self.estimate_date_input)
        layout.addWidget(self.expiration_date_input)

        return layout

    def build_items_table(self) -> QTableWidget:
        self.items_table = QTableWidget(0, 4)
        self.items_table.setObjectName("estimateTable")
        self.items_table.setHorizontalHeaderLabels(
            ["Description", "Qty", "Rate", "Amount"]
        )

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(
            self.DESCRIPTION_COLUMN,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            self.QUANTITY_COLUMN,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            self.RATE_COLUMN,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            self.AMOUNT_COLUMN,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.items_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)

        return self.items_table

    def build_item_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        add_service_button = QPushButton("+ Add Service")
        add_service_button.setObjectName("primaryButton")
        add_service_button.setMinimumHeight(40)
        add_service_button.clicked.connect(self.choose_service)

        add_custom_button = QPushButton("+ Custom Line Item")
        add_custom_button.setObjectName("secondaryButton")
        add_custom_button.clicked.connect(self.add_line_item)

        remove_button = QPushButton("Remove Selected")
        remove_button.setObjectName("dangerButton")
        remove_button.clicked.connect(self.remove_selected_item)

        layout.addWidget(add_service_button)
        layout.addWidget(add_custom_button)
        layout.addWidget(remove_button)
        layout.addStretch()

        return layout

    def choose_service(self) -> None:
        dialog = ServiceSelectionDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if dialog.selected_service is None:
            return

        item = estimate_item_from_service(dialog.selected_service)
        self.add_line_item(item)
        self.recalculate_totals()

    def build_bottom_section(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(20)

        left = QVBoxLayout()

        job_label = QLabel("Job Address")
        job_label.setObjectName("metricTitle")

        self.job_address_input = QLineEdit()
        self.job_address_input.setObjectName("formInput")

        notes_label = QLabel("Estimate Notes")
        notes_label.setObjectName("metricTitle")

        self.notes_input = QTextEdit()
        self.notes_input.setObjectName("formInput")
        self.notes_input.setPlaceholderText(
            "Example: Materials and labor included."
        )
        self.notes_input.setFixedHeight(85)

        left.addWidget(job_label)
        left.addWidget(self.job_address_input)
        left.addWidget(notes_label)
        left.addWidget(self.notes_input)

        totals = QFrame()
        totals.setObjectName("totalsPanel")
        totals.setFixedWidth(320)

        totals_layout = QVBoxLayout(totals)
        totals_layout.setContentsMargins(18, 16, 18, 16)
        totals_layout.setSpacing(10)

        self.subtotal_label = QLabel("Subtotal: $0.00")
        self.subtotal_label.setObjectName("totalLine")

        tax_row = QHBoxLayout()
        tax_title = QLabel("Tax Rate")
        tax_title.setObjectName("totalLine")

        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setObjectName("formInput")
        self.tax_rate_input.setRange(0.0, 100.0)
        self.tax_rate_input.setDecimals(2)
        self.tax_rate_input.setSuffix("%")
        self.tax_rate_input.valueChanged.connect(self.recalculate_totals)

        tax_row.addWidget(tax_title)
        tax_row.addStretch()
        tax_row.addWidget(self.tax_rate_input)

        self.tax_label = QLabel("Tax: $0.00")
        self.tax_label.setObjectName("totalLine")

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setObjectName("grandTotal")

        preview_button = QPushButton("Preview PDF")
        preview_button.setObjectName("secondaryButton")
        preview_button.setMinimumHeight(42)
        preview_button.clicked.connect(self.preview_pdf)

        save_button = QPushButton("Save Estimate")
        save_button.setObjectName("primaryButton")
        save_button.setMinimumHeight(42)
        save_button.clicked.connect(self.save_estimate)

        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addLayout(tax_row)
        totals_layout.addWidget(self.tax_label)
        totals_layout.addWidget(self.total_label)
        totals_layout.addSpacing(8)
        totals_layout.addWidget(preview_button)
        totals_layout.addWidget(save_button)

        layout.addLayout(left, 1)
        layout.addWidget(totals)

        return layout

    def load_customers(self) -> None:
        current_id = self.customer_combo.currentData()

        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        self.customer_combo.addItem("Select customer...", None)

        for customer in self.customer_repository.get_all():
            label = customer.name
            if customer.company:
                label += f" — {customer.company}"

            self.customer_combo.addItem(label, customer.id)

        if current_id is not None:
            index = self.customer_combo.findData(current_id)
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)

        self.customer_combo.blockSignals(False)

    def start_new_estimate(self) -> None:
        self.current_estimate_id = None
        self.load_customers()
        self.load_saved_estimates()

        self.number_input.setValue(
            self.estimate_repository.next_estimate_number()
        )

        today = date.today()
        settings = self.settings_repository.get()
        expiration = today + timedelta(days=settings.estimate_expiration_days)

        self.estimate_date_input.setDate(
            QDate(today.year, today.month, today.day)
        )
        self.expiration_date_input.setDate(
            QDate(expiration.year, expiration.month, expiration.day)
        )

        self.customer_combo.setCurrentIndex(0)
        self.job_address_input.clear()
        self.notes_input.setPlainText(settings.default_estimate_notes)
        self.tax_rate_input.setValue(0.0)
        self.items_table.setRowCount(0)

        self.add_line_item()
        self.recalculate_totals()

    def create_customer(self) -> None:
        dialog = CustomerDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        customer = dialog.created_customer

        if customer is None:
            return

        self.load_customers()

        index = self.customer_combo.findData(customer.id)

        if index >= 0:
            self.customer_combo.setCurrentIndex(index)

        self.job_address_input.setText(customer.job_address)

    def customer_changed(self) -> None:
        customer_id = self.customer_combo.currentData()

        if customer_id is None:
            return

        customer = self.customer_repository.get_by_id(customer_id)

        if customer is not None:
            self.job_address_input.setText(customer.job_address)

    def load_saved_estimates(self) -> None:
        if not hasattr(self, "saved_estimates_combo"):
            return

        current_id = self.saved_estimates_combo.currentData()

        self.saved_estimates_combo.clear()
        self.saved_estimates_combo.addItem("Select saved estimate...", None)

        for summary in self.estimate_repository.get_all_summaries():
            customer = summary["customer_name"]

            if summary["customer_company"]:
                customer += f" — {summary['customer_company']}"

            total = self.format_currency(summary["total_cents"])

            label = (
                f"Estimate #{summary['estimate_number']} | "
                f"{customer} | {total}"
            )

            self.saved_estimates_combo.addItem(label, summary["id"])

        if current_id is not None:
            index = self.saved_estimates_combo.findData(current_id)
            if index >= 0:
                self.saved_estimates_combo.setCurrentIndex(index)

    def open_saved_estimate(self) -> None:
        estimate_id = self.saved_estimates_combo.currentData()

        if estimate_id is None:
            QMessageBox.information(
                self,
                "Select an Estimate",
                "Choose a saved estimate before clicking Open.",
            )
            return

        estimate = self.estimate_repository.get_by_id(estimate_id)

        if estimate is None:
            QMessageBox.warning(
                self,
                "Estimate Not Found",
                "The selected estimate could not be loaded.",
            )
            self.load_saved_estimates()
            return

        self.current_estimate_id = estimate.id
        self.number_input.setValue(estimate.estimate_number)

        customer_index = self.customer_combo.findData(
            estimate.customer_id
        )
        if customer_index >= 0:
            self.customer_combo.setCurrentIndex(customer_index)

        self.estimate_date_input.setDate(
            QDate.fromString(estimate.estimate_date, "yyyy-MM-dd")
        )
        self.expiration_date_input.setDate(
            QDate.fromString(estimate.expiration_date, "yyyy-MM-dd")
        )

        self.job_address_input.setText(estimate.job_address)
        self.notes_input.setPlainText(estimate.notes)
        self.tax_rate_input.setValue(estimate.tax_rate)

        self.items_table.setRowCount(0)

        for item in estimate.items:
            self.add_line_item(item)

        if not estimate.items:
            self.add_line_item()

        self.recalculate_totals()

    def delete_current_estimate(self) -> None:
        estimate_id = self.current_estimate_id

        if estimate_id is None:
            estimate_id = self.saved_estimates_combo.currentData()

        if estimate_id is None:
            QMessageBox.information(
                self,
                "No Estimate Selected",
                "Open or select an estimate before deleting.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Estimate",
            "Are you sure you want to permanently delete this estimate?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.estimate_repository.delete(estimate_id)
        self.start_new_estimate()

    def convert_to_invoice(self) -> None:
        estimate_id = self.current_estimate_id or self.saved_estimates_combo.currentData()
        if estimate_id is None:
            QMessageBox.information(
                self,
                "No Estimate Selected",
                "Open or select a saved estimate before converting.",
            )
            return
        estimate = self.estimate_repository.get_by_id(estimate_id)
        if estimate is None:
            QMessageBox.warning(
                self, "Estimate Not Found", "The selected estimate could not be loaded."
            )
            return

        try:
            invoice = self.invoice_repository.create_from_estimate(estimate)
        except DuplicateEstimateConversionError as error:
            answer = QMessageBox.question(
                self,
                "Estimate Already Converted",
                f"{error}\n\nCreate another invoice anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            try:
                invoice = self.invoice_repository.create_from_estimate(
                    estimate, allow_duplicate=True
                )
            except Exception as retry_error:
                QMessageBox.critical(
                    self, "Unable to Convert Estimate", str(retry_error)
                )
                return
        except Exception as error:
            QMessageBox.critical(self, "Unable to Convert Estimate", str(error))
            return

        QMessageBox.information(
            self,
            "Invoice Created",
            f"Invoice #{invoice.invoice_number} was created from "
            f"estimate #{estimate.estimate_number}.",
        )
        self.invoice_created.emit(invoice.id)

    def add_line_item(
        self,
        existing_item: EstimateItem | None = None,
    ) -> None:
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        description = QLineEdit()
        description.setPlaceholderText("Describe the work or service")
        description.setObjectName("tableInput")

        quantity = QDoubleSpinBox()
        quantity.setRange(0.01, 999999.0)
        quantity.setDecimals(2)
        quantity.setValue(
            existing_item.quantity if existing_item else 1.0
        )
        quantity.setObjectName("tableInput")

        rate = QDoubleSpinBox()
        rate.setRange(0.0, 99999999.99)
        rate.setDecimals(2)
        rate.setPrefix("$")
        rate.setObjectName("tableInput")

        if existing_item is not None:
            description.setText(existing_item.description)
            rate.setValue(existing_item.rate_cents / 100)

        amount = QTableWidgetItem("$0.00")
        amount.setTextAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        amount.setFlags(
            amount.flags() & ~Qt.ItemFlag.ItemIsEditable
        )

        quantity.valueChanged.connect(self.recalculate_totals)
        rate.valueChanged.connect(self.recalculate_totals)

        self.items_table.setCellWidget(
            row,
            self.DESCRIPTION_COLUMN,
            description,
        )
        self.items_table.setCellWidget(
            row,
            self.QUANTITY_COLUMN,
            quantity,
        )
        self.items_table.setCellWidget(
            row,
            self.RATE_COLUMN,
            rate,
        )
        self.items_table.setItem(
            row,
            self.AMOUNT_COLUMN,
            amount,
        )

        self.items_table.setRowHeight(row, 42)
        description.setFocus()

    def remove_selected_item(self) -> None:
        selected_rows = sorted(
            {
                index.row()
                for index in self.items_table.selectedIndexes()
            },
            reverse=True,
        )

        if not selected_rows and self.items_table.rowCount() > 0:
            selected_rows = [self.items_table.rowCount() - 1]

        for row in selected_rows:
            self.items_table.removeRow(row)

        if self.items_table.rowCount() == 0:
            self.add_line_item()

        self.recalculate_totals()

    def collect_items(self) -> list[EstimateItem]:
        items: list[EstimateItem] = []

        for row in range(self.items_table.rowCount()):
            description_widget = self.items_table.cellWidget(
                row,
                self.DESCRIPTION_COLUMN,
            )
            quantity_widget = self.items_table.cellWidget(
                row,
                self.QUANTITY_COLUMN,
            )
            rate_widget = self.items_table.cellWidget(
                row,
                self.RATE_COLUMN,
            )

            description = description_widget.text().strip()
            quantity = quantity_widget.value()
            rate_cents = round(rate_widget.value() * 100)
            amount_cents = round(quantity * rate_cents)

            if not description and rate_cents == 0:
                continue

            items.append(
                EstimateItem(
                    description=description,
                    quantity=quantity,
                    rate_cents=rate_cents,
                    amount_cents=amount_cents,
                )
            )

        return items

    def recalculate_totals(self) -> None:
        subtotal_cents = 0

        for row in range(self.items_table.rowCount()):
            quantity_widget = self.items_table.cellWidget(
                row,
                self.QUANTITY_COLUMN,
            )
            rate_widget = self.items_table.cellWidget(
                row,
                self.RATE_COLUMN,
            )

            if quantity_widget is None or rate_widget is None:
                continue

            amount_cents = round(
                quantity_widget.value()
                * rate_widget.value()
                * 100
            )

            subtotal_cents += amount_cents

            amount_item = self.items_table.item(
                row,
                self.AMOUNT_COLUMN,
            )
            if amount_item is not None:
                amount_item.setText(
                    self.format_currency(amount_cents)
                )

        tax_rate = self.tax_rate_input.value()
        tax_cents = round(subtotal_cents * tax_rate / 100)
        total_cents = subtotal_cents + tax_cents

        self.subtotal_label.setText(
            f"Subtotal: {self.format_currency(subtotal_cents)}"
        )
        self.tax_label.setText(
            f"Tax: {self.format_currency(tax_cents)}"
        )
        self.total_label.setText(
            f"Total: {self.format_currency(total_cents)}"
        )

    def preview_pdf(self) -> None:
        customer_id = self.customer_combo.currentData()

        if customer_id is None:
            QMessageBox.warning(
                self,
                "Customer Required",
                "Select a customer before creating the PDF.",
            )
            return

        customer = self.customer_repository.get_by_id(customer_id)

        if customer is None:
            QMessageBox.warning(
                self,
                "Customer Not Found",
                "The selected customer could not be loaded.",
            )
            return

        items = self.collect_items()

        if not items:
            QMessageBox.warning(
                self,
                "Line Item Required",
                "Add at least one estimate line item.",
            )
            return

        for item in items:
            if not item.description:
                QMessageBox.warning(
                    self,
                    "Description Required",
                    "Every priced line item needs a description.",
                )
                return

        subtotal_cents = sum(item.amount_cents for item in items)
        tax_rate = self.tax_rate_input.value()
        tax_cents = round(subtotal_cents * tax_rate / 100)
        total_cents = subtotal_cents + tax_cents

        estimate_date = self.estimate_date_input.date()
        expiration_date = self.expiration_date_input.date()

        estimate = Estimate(
            id=self.current_estimate_id,
            estimate_number=self.number_input.value(),
            customer_id=customer_id,
            estimate_date=estimate_date.toString("MM/dd/yyyy"),
            expiration_date=expiration_date.toString("MM/dd/yyyy"),
            job_address=self.job_address_input.text().strip(),
            notes=self.notes_input.toPlainText().strip(),
            subtotal_cents=subtotal_cents,
            tax_rate=tax_rate,
            tax_cents=tax_cents,
            total_cents=total_cents,
            items=items,
        )

        try:
            pdf_path = generate_estimate_pdf(estimate, customer)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to Generate PDF",
                str(error),
            )
            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(pdf_path))
        )

        if not opened:
            QMessageBox.information(
                self,
                "PDF Created",
                f"The PDF was saved here:\n{pdf_path}",
            )

    def save_estimate(self) -> None:
        customer_id = self.customer_combo.currentData()

        if customer_id is None:
            QMessageBox.warning(
                self,
                "Customer Required",
                "Select a customer before saving the estimate.",
            )
            self.customer_combo.setFocus()
            return

        items = self.collect_items()

        if not items:
            QMessageBox.warning(
                self,
                "Line Item Required",
                "Add at least one estimate line item.",
            )
            return

        for item in items:
            if not item.description:
                QMessageBox.warning(
                    self,
                    "Description Required",
                    "Every priced line item needs a description.",
                )
                return

        subtotal_cents = sum(item.amount_cents for item in items)
        tax_rate = self.tax_rate_input.value()
        tax_cents = round(subtotal_cents * tax_rate / 100)
        total_cents = subtotal_cents + tax_cents

        estimate_date = self.estimate_date_input.date()
        expiration_date = self.expiration_date_input.date()

        estimate = Estimate(
            id=self.current_estimate_id,
            estimate_number=self.number_input.value(),
            customer_id=customer_id,
            estimate_date=estimate_date.toString("yyyy-MM-dd"),
            expiration_date=expiration_date.toString("yyyy-MM-dd"),
            job_address=self.job_address_input.text().strip(),
            notes=self.notes_input.toPlainText().strip(),
            subtotal_cents=subtotal_cents,
            tax_rate=tax_rate,
            tax_cents=tax_cents,
            total_cents=total_cents,
            items=items,
        )

        try:
            if estimate.id is None:
                self.estimate_repository.create(estimate)
                action = "saved"
            else:
                self.estimate_repository.update(estimate)
                action = "updated"
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to Save Estimate",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Estimate Saved",
            (
                f"Estimate #{estimate.estimate_number} was {action} "
                f"successfully for "
                f"{self.format_currency(estimate.total_cents)}."
            ),
        )

        self.start_new_estimate()

    @staticmethod
    def format_currency(cents: int) -> str:
        return f"${cents / 100:,.2f}"
