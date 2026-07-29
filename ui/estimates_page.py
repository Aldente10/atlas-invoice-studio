from datetime import date, timedelta

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
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
from models.estimate import Estimate, EstimateItem


class EstimatesPage(QWidget):
    DESCRIPTION_COLUMN = 0
    QUANTITY_COLUMN = 1
    RATE_COLUMN = 2
    AMOUNT_COLUMN = 3

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboard")

        self.customer_repository = CustomerRepository()
        self.estimate_repository = EstimateRepository()

        self.build_ui()
        self.load_customers()
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

        self.customer_combo = QComboBox()
        self.customer_combo.setObjectName("formInput")
        self.customer_combo.setMinimumWidth(240)
        self.customer_combo.currentIndexChanged.connect(
            self.customer_changed
        )

        self.estimate_date_input = QDateEdit()
        self.estimate_date_input.setObjectName("formInput")
        self.estimate_date_input.setCalendarPopup(True)
        self.estimate_date_input.setDisplayFormat("MM/dd/yyyy")

        self.expiration_date_input = QDateEdit()
        self.expiration_date_input.setObjectName("formInput")
        self.expiration_date_input.setCalendarPopup(True)
        self.expiration_date_input.setDisplayFormat("MM/dd/yyyy")

        layout.addWidget(self.number_input)
        layout.addWidget(self.customer_combo, 1)
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

        add_button = QPushButton("+ Add Line Item")
        add_button.setObjectName("secondaryButton")
        add_button.clicked.connect(self.add_line_item)

        remove_button = QPushButton("Remove Selected")
        remove_button.setObjectName("dangerButton")
        remove_button.clicked.connect(self.remove_selected_item)

        layout.addWidget(add_button)
        layout.addWidget(remove_button)
        layout.addStretch()

        return layout

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

        save_button = QPushButton("Save Estimate")
        save_button.setObjectName("primaryButton")
        save_button.setMinimumHeight(42)
        save_button.clicked.connect(self.save_estimate)

        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addLayout(tax_row)
        totals_layout.addWidget(self.tax_label)
        totals_layout.addWidget(self.total_label)
        totals_layout.addSpacing(8)
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
        self.load_customers()

        self.number_input.setValue(
            self.estimate_repository.next_estimate_number()
        )

        today = date.today()
        expiration = today + timedelta(days=14)

        self.estimate_date_input.setDate(
            QDate(today.year, today.month, today.day)
        )
        self.expiration_date_input.setDate(
            QDate(expiration.year, expiration.month, expiration.day)
        )

        self.customer_combo.setCurrentIndex(0)
        self.job_address_input.clear()
        self.notes_input.setPlainText("Materials and labor included.")
        self.tax_rate_input.setValue(0.0)
        self.items_table.setRowCount(0)

        self.add_line_item()
        self.recalculate_totals()

    def customer_changed(self) -> None:
        customer_id = self.customer_combo.currentData()

        if customer_id is None:
            return

        customer = self.customer_repository.get_by_id(customer_id)

        if customer is not None:
            self.job_address_input.setText(customer.job_address)

    def add_line_item(self) -> None:
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        description = QLineEdit()
        description.setPlaceholderText("Describe the work or service")
        description.setObjectName("tableInput")

        quantity = QDoubleSpinBox()
        quantity.setRange(0.01, 999999.0)
        quantity.setDecimals(2)
        quantity.setValue(1.0)
        quantity.setObjectName("tableInput")

        rate = QDoubleSpinBox()
        rate.setRange(0.0, 99999999.99)
        rate.setDecimals(2)
        rate.setPrefix("$")
        rate.setObjectName("tableInput")

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
            self.estimate_repository.create(estimate)
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
                f"Estimate #{estimate.estimate_number} was saved "
                f"successfully for "
                f"{self.format_currency(estimate.total_cents)}."
            ),
        )

        self.start_new_estimate()

    @staticmethod
    def format_currency(cents: int) -> str:
        return f"${cents / 100:,.2f}"
