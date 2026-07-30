from datetime import date, timedelta

from PySide6.QtCore import QDate, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.customer_repository import CustomerRepository
from database.invoice_repository import InvoiceRepository
from models.invoice import INVOICE_STATUSES, Invoice, InvoiceItem
from pdf.invoice_pdf import generate_invoice_pdf
from services.estimate_items import estimate_item_from_service
from ui.estimates_page import EstimatesPage
from ui.service_selection_dialog import ServiceSelectionDialog


class InvoicesPage(EstimatesPage):
    """Invoice editor sharing the estimate page's line-item controls."""

    def __init__(self) -> None:
        QWidget.__init__(self)
        self.setObjectName("dashboard")
        self.customer_repository = CustomerRepository()
        self.invoice_repository = InvoiceRepository()
        self.current_invoice_id: int | None = None

        self.build_ui()
        self.load_customers()
        self.load_saved_invoices()
        self.start_new_invoice()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        heading_group = QVBoxLayout()
        heading_group.setSpacing(2)
        heading = QLabel("Invoices")
        heading.setObjectName("pageHeading")
        subtitle = QLabel(
            "Create, update, and track invoices with professional PDF output."
        )
        subtitle.setObjectName("pageSubtitle")
        heading_group.addWidget(heading)
        heading_group.addWidget(subtitle)

        new_button = QPushButton("+ New Invoice")
        new_button.setObjectName("primaryButton")
        new_button.setFixedSize(145, 42)
        new_button.clicked.connect(self.start_new_invoice)
        header.addLayout(heading_group)
        header.addStretch()
        header.addWidget(new_button)
        root.addLayout(header)

        saved_row = QHBoxLayout()
        saved_label = QLabel("Open Saved Invoice")
        saved_label.setObjectName("metricTitle")
        self.saved_invoices_combo = QComboBox()
        self.saved_invoices_combo.setObjectName("formInput")
        self.saved_invoices_combo.setMinimumWidth(420)
        open_button = QPushButton("Open")
        open_button.setObjectName("secondaryButton")
        open_button.clicked.connect(self.open_saved_invoice)
        delete_button = QPushButton("Delete Invoice")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_current_invoice)
        saved_row.addWidget(saved_label)
        saved_row.addWidget(self.saved_invoices_combo)
        saved_row.addWidget(open_button)
        saved_row.addWidget(delete_button)
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
        layout.setSpacing(12)

        self.number_input = QSpinBox()
        self.number_input.setRange(1, 999999)
        self.number_input.setObjectName("formInput")
        self.number_input.setPrefix("Invoice #")

        customer_widget = QWidget()
        customer_layout = QHBoxLayout(customer_widget)
        customer_layout.setContentsMargins(0, 0, 0, 0)
        customer_layout.setSpacing(6)
        self.customer_combo = QComboBox()
        self.customer_combo.setObjectName("formInput")
        self.customer_combo.setMinimumWidth(220)
        self.customer_combo.currentIndexChanged.connect(self.customer_changed)
        add_customer = QPushButton("+ Customer")
        add_customer.setObjectName("secondaryButton")
        add_customer.clicked.connect(self.create_customer)
        customer_layout.addWidget(self.customer_combo, 1)
        customer_layout.addWidget(add_customer)

        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setObjectName("formInput")
        self.invoice_date_input.setCalendarPopup(True)
        self.invoice_date_input.setDisplayFormat("MM/dd/yyyy")
        self.due_date_input = QDateEdit()
        self.due_date_input.setObjectName("formInput")
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDisplayFormat("MM/dd/yyyy")
        self.status_input = QComboBox()
        self.status_input.setObjectName("formInput")
        self.status_input.addItems(INVOICE_STATUSES)

        layout.addWidget(self.number_input)
        layout.addWidget(customer_widget, 1)
        layout.addWidget(self.invoice_date_input)
        layout.addWidget(self.due_date_input)
        layout.addWidget(self.status_input)
        return layout

    def build_bottom_section(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(20)
        left = QVBoxLayout()
        job_label = QLabel("Job Address")
        job_label.setObjectName("metricTitle")
        self.job_address_input = QLineEdit()
        self.job_address_input.setObjectName("formInput")
        notes_label = QLabel("Invoice Notes")
        notes_label.setObjectName("metricTitle")
        self.notes_input = QTextEdit()
        self.notes_input.setObjectName("formInput")
        self.notes_input.setPlaceholderText("Example: Thank you for your business.")
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
        preview = QPushButton("Preview PDF")
        preview.setObjectName("secondaryButton")
        preview.setMinimumHeight(42)
        preview.clicked.connect(self.preview_pdf)
        save = QPushButton("Save Invoice")
        save.setObjectName("primaryButton")
        save.setMinimumHeight(42)
        save.clicked.connect(self.save_invoice)
        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addLayout(tax_row)
        totals_layout.addWidget(self.tax_label)
        totals_layout.addWidget(self.total_label)
        totals_layout.addSpacing(8)
        totals_layout.addWidget(preview)
        totals_layout.addWidget(save)
        layout.addLayout(left, 1)
        layout.addWidget(totals)
        return layout

    def choose_service(self) -> None:
        dialog = ServiceSelectionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if dialog.selected_service is None:
            return
        estimate_item = estimate_item_from_service(dialog.selected_service)
        self.add_line_item(
            InvoiceItem(
                description=estimate_item.description,
                quantity=estimate_item.quantity,
                rate_cents=estimate_item.rate_cents,
                amount_cents=estimate_item.amount_cents,
            )
        )
        self.recalculate_totals()

    def start_new_invoice(self) -> None:
        self.current_invoice_id = None
        self.load_customers()
        self.load_saved_invoices()
        self.number_input.setValue(self.invoice_repository.next_invoice_number())
        today = date.today()
        due = today + timedelta(days=30)
        self.invoice_date_input.setDate(QDate(today.year, today.month, today.day))
        self.due_date_input.setDate(QDate(due.year, due.month, due.day))
        self.customer_combo.setCurrentIndex(0)
        self.status_input.setCurrentText("Draft")
        self.job_address_input.clear()
        self.notes_input.setPlainText("Thank you for your business.")
        self.tax_rate_input.setValue(0.0)
        self.items_table.setRowCount(0)
        self.add_line_item()
        self.recalculate_totals()

    def load_saved_invoices(self) -> None:
        if not hasattr(self, "saved_invoices_combo"):
            return
        current_id = self.saved_invoices_combo.currentData()
        self.saved_invoices_combo.clear()
        self.saved_invoices_combo.addItem("Select saved invoice...", None)
        for summary in self.invoice_repository.get_all_summaries():
            customer = summary["customer_name"]
            if summary["customer_company"]:
                customer += f" — {summary['customer_company']}"
            label = (
                f"Invoice #{summary['invoice_number']} | {customer} | "
                f"{self.format_currency(summary['total_cents'])} | "
                f"{summary['status']}"
            )
            self.saved_invoices_combo.addItem(label, summary["id"])
        if current_id is not None:
            index = self.saved_invoices_combo.findData(current_id)
            if index >= 0:
                self.saved_invoices_combo.setCurrentIndex(index)

    def open_saved_invoice(self) -> None:
        invoice_id = self.saved_invoices_combo.currentData()
        if invoice_id is None:
            QMessageBox.information(
                self, "Select an Invoice", "Choose a saved invoice before clicking Open."
            )
            return
        self.open_invoice(invoice_id)

    def open_invoice(self, invoice_id: int) -> None:
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if invoice is None:
            QMessageBox.warning(
                self, "Invoice Not Found", "The selected invoice could not be loaded."
            )
            self.load_saved_invoices()
            return
        self.load_customers()
        self.current_invoice_id = invoice.id
        self.number_input.setValue(invoice.invoice_number)
        customer_index = self.customer_combo.findData(invoice.customer_id)
        if customer_index >= 0:
            self.customer_combo.setCurrentIndex(customer_index)
        self.invoice_date_input.setDate(
            QDate.fromString(invoice.invoice_date, "yyyy-MM-dd")
        )
        self.due_date_input.setDate(QDate.fromString(invoice.due_date, "yyyy-MM-dd"))
        self.status_input.setCurrentText(invoice.status)
        self.job_address_input.setText(invoice.job_address)
        self.notes_input.setPlainText(invoice.notes)
        self.tax_rate_input.setValue(invoice.tax_rate)
        self.items_table.setRowCount(0)
        for item in invoice.items:
            self.add_line_item(item)
        if not invoice.items:
            self.add_line_item()
        self.recalculate_totals()
        index = self.saved_invoices_combo.findData(invoice.id)
        if index >= 0:
            self.saved_invoices_combo.setCurrentIndex(index)

    def delete_current_invoice(self) -> None:
        invoice_id = self.current_invoice_id or self.saved_invoices_combo.currentData()
        if invoice_id is None:
            QMessageBox.information(
                self, "No Invoice Selected", "Open or select an invoice before deleting."
            )
            return
        answer = QMessageBox.question(
            self,
            "Delete Invoice",
            "Are you sure you want to permanently delete this invoice?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.invoice_repository.delete(invoice_id)
        self.start_new_invoice()

    def collect_items(self) -> list[InvoiceItem]:
        items = []
        for row in range(self.items_table.rowCount()):
            description = self.items_table.cellWidget(row, self.DESCRIPTION_COLUMN).text().strip()
            quantity = self.items_table.cellWidget(row, self.QUANTITY_COLUMN).value()
            rate_cents = round(
                self.items_table.cellWidget(row, self.RATE_COLUMN).value() * 100
            )
            if not description and rate_cents == 0:
                continue
            items.append(
                InvoiceItem(
                    description=description,
                    quantity=quantity,
                    rate_cents=rate_cents,
                    amount_cents=round(quantity * rate_cents),
                )
            )
        return items

    def _build_invoice(self, *, display_dates: bool = False) -> Invoice | None:
        customer_id = self.customer_combo.currentData()
        if customer_id is None:
            QMessageBox.warning(self, "Customer Required", "Select a customer first.")
            return None
        items = self.collect_items()
        if not items:
            QMessageBox.warning(
                self, "Line Item Required", "Add at least one invoice line item."
            )
            return None
        if any(not item.description for item in items):
            QMessageBox.warning(
                self,
                "Description Required",
                "Every priced line item needs a description.",
            )
            return None
        subtotal_cents = sum(item.amount_cents for item in items)
        tax_rate = self.tax_rate_input.value()
        tax_cents = round(subtotal_cents * tax_rate / 100)
        date_format = "MM/dd/yyyy" if display_dates else "yyyy-MM-dd"
        existing = (
            self.invoice_repository.get_by_id(self.current_invoice_id)
            if self.current_invoice_id is not None
            else None
        )
        return Invoice(
            id=self.current_invoice_id,
            invoice_number=self.number_input.value(),
            customer_id=customer_id,
            source_estimate_id=existing.source_estimate_id if existing else None,
            invoice_date=self.invoice_date_input.date().toString(date_format),
            due_date=self.due_date_input.date().toString(date_format),
            job_address=self.job_address_input.text().strip(),
            notes=self.notes_input.toPlainText().strip(),
            subtotal_cents=subtotal_cents,
            tax_rate=tax_rate,
            tax_cents=tax_cents,
            total_cents=subtotal_cents + tax_cents,
            status=self.status_input.currentText(),
            items=items,
        )

    def preview_pdf(self) -> None:
        invoice = self._build_invoice(display_dates=True)
        if invoice is None:
            return
        customer = self.customer_repository.get_by_id(invoice.customer_id)
        if customer is None:
            QMessageBox.warning(
                self, "Customer Not Found", "The selected customer could not be loaded."
            )
            return
        try:
            pdf_path = generate_invoice_pdf(invoice, customer)
        except Exception as error:
            QMessageBox.critical(self, "Unable to Generate PDF", str(error))
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path))):
            QMessageBox.information(
                self, "PDF Created", f"The PDF was saved here:\n{pdf_path}"
            )

    def save_invoice(self) -> None:
        invoice = self._build_invoice()
        if invoice is None:
            return
        try:
            if invoice.id is None:
                self.invoice_repository.create(invoice)
                action = "saved"
            else:
                self.invoice_repository.update(invoice)
                action = "updated"
        except Exception as error:
            QMessageBox.critical(self, "Unable to Save Invoice", str(error))
            return
        QMessageBox.information(
            self,
            "Invoice Saved",
            f"Invoice #{invoice.invoice_number} was {action} successfully for "
            f"{self.format_currency(invoice.total_cents)}.",
        )
        self.start_new_invoice()
