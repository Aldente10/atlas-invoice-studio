from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.customer_repository import CustomerRepository
from models.customer import Customer


class CustomersPage(QWidget):
    data_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboard")

        self.repository = CustomerRepository()
        self.current_customer_id: int | None = None

        self.build_ui()
        self.load_customers()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        header = QHBoxLayout()

        heading_group = QVBoxLayout()
        heading_group.setSpacing(2)

        heading = QLabel("Customers")
        heading.setObjectName("pageHeading")

        subtitle = QLabel(
            "Manage customer contact information and job locations."
        )
        subtitle.setObjectName("pageSubtitle")

        heading_group.addWidget(heading)
        heading_group.addWidget(subtitle)

        self.new_button = QPushButton("+ New Customer")
        self.new_button.setObjectName("primaryButton")
        self.new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_button.setFixedSize(150, 42)
        self.new_button.clicked.connect(self.clear_form)

        header.addLayout(heading_group)
        header.addStretch()
        header.addWidget(self.new_button)

        root.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(16)

        content.addWidget(self.build_customer_list_panel(), 1)
        content.addWidget(self.build_customer_form_panel(), 2)

        root.addLayout(content, 1)

    def build_customer_list_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Customer List")
        title.setObjectName("panelTitle")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers...")
        self.search_input.setObjectName("formInput")
        self.search_input.textChanged.connect(self.search_customers)

        self.customer_list = QListWidget()
        self.customer_list.setObjectName("customerList")
        self.customer_list.itemSelectionChanged.connect(
            self.load_selected_customer
        )

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.customer_list, 1)

        return panel

    def build_customer_form_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)

        title = QLabel("Customer Details")
        title.setObjectName("panelTitle")

        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.name_input = QLineEdit()
        self.company_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()

        self.billing_address_input = QTextEdit()
        self.job_address_input = QTextEdit()
        self.notes_input = QTextEdit()

        self.billing_address_input.setFixedHeight(75)
        self.job_address_input.setFixedHeight(75)
        self.notes_input.setFixedHeight(90)

        inputs = [
            self.name_input,
            self.company_input,
            self.phone_input,
            self.email_input,
            self.billing_address_input,
            self.job_address_input,
            self.notes_input,
        ]

        for widget in inputs:
            widget.setObjectName("formInput")

        form.addRow("Name *", self.name_input)
        form.addRow("Company", self.company_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Billing Address", self.billing_address_input)
        form.addRow("Job Address", self.job_address_input)
        form.addRow("Notes", self.notes_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_customer)

        self.cancel_button = QPushButton("Clear")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.clear_form)

        self.save_button = QPushButton("Save Customer")
        self.save_button.setObjectName("primaryButton")
        self.save_button.setFixedSize(145, 40)
        self.save_button.clicked.connect(self.save_customer)

        buttons.addWidget(self.delete_button)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout.addStretch()
        layout.addLayout(buttons)

        return panel

    def load_customers(self, customers: list[Customer] | None = None) -> None:
        self.customer_list.clear()

        if customers is None:
            customers = self.repository.get_all()

        for customer in customers:
            display_text = customer.name
            if customer.company:
                display_text += f"\n{customer.company}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, customer.id)
            self.customer_list.addItem(item)

    def search_customers(self, text: str) -> None:
        if text.strip():
            customers = self.repository.search(text)
        else:
            customers = self.repository.get_all()

        self.load_customers(customers)

    def load_selected_customer(self) -> None:
        selected_items = self.customer_list.selectedItems()
        if not selected_items:
            return

        customer_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        customer = self.repository.get_by_id(customer_id)

        if customer is None:
            return

        self.current_customer_id = customer.id
        self.name_input.setText(customer.name)
        self.company_input.setText(customer.company)
        self.phone_input.setText(customer.phone)
        self.email_input.setText(customer.email)
        self.billing_address_input.setPlainText(customer.billing_address)
        self.job_address_input.setPlainText(customer.job_address)
        self.notes_input.setPlainText(customer.notes)

    def save_customer(self) -> None:
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Missing Customer Name",
                "Please enter the customer's name.",
            )
            self.name_input.setFocus()
            return

        customer = Customer(
            id=self.current_customer_id,
            name=name,
            company=self.company_input.text().strip(),
            phone=self.phone_input.text().strip(),
            email=self.email_input.text().strip(),
            billing_address=self.billing_address_input.toPlainText().strip(),
            job_address=self.job_address_input.toPlainText().strip(),
            notes=self.notes_input.toPlainText().strip(),
        )

        if customer.id is None:
            saved_customer = self.repository.create(customer)
            self.current_customer_id = saved_customer.id
            message = "Customer created successfully."
        else:
            self.repository.update(customer)
            message = "Customer updated successfully."

        self.load_customers()
        self.data_changed.emit()
        QMessageBox.information(self, "Saved", message)

    def delete_customer(self) -> None:
        if self.current_customer_id is None:
            QMessageBox.information(
                self,
                "No Customer Selected",
                "Select a customer before deleting.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Customer",
            "Are you sure you want to delete this customer?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.repository.delete(self.current_customer_id)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to Delete Customer",
                "This customer may be linked to an estimate or invoice.\n\n"
                f"Details: {error}",
            )
            return
        self.clear_form()
        self.load_customers()
        self.data_changed.emit()

    def clear_form(self) -> None:
        self.current_customer_id = None
        self.customer_list.clearSelection()

        self.name_input.clear()
        self.company_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.billing_address_input.clear()
        self.job_address_input.clear()
        self.notes_input.clear()

        self.name_input.setFocus()
