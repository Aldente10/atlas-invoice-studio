from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from database.customer_repository import CustomerRepository
from models.customer import Customer


class CustomerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.repository = CustomerRepository()
        self.created_customer: Customer | None = None

        self.setWindowTitle("New Customer")
        self.setMinimumWidth(520)

        self.build_ui()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)

        self.name_input = QLineEdit()
        self.company_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.billing_address_input = QTextEdit()
        self.job_address_input = QTextEdit()
        self.notes_input = QTextEdit()

        self.billing_address_input.setFixedHeight(65)
        self.job_address_input.setFixedHeight(65)
        self.notes_input.setFixedHeight(75)

        widgets = [
            self.name_input,
            self.company_input,
            self.phone_input,
            self.email_input,
            self.billing_address_input,
            self.job_address_input,
            self.notes_input,
        ]

        for widget in widgets:
            widget.setObjectName("formInput")

        form.addRow("Name *", self.name_input)
        form.addRow("Company", self.company_input)
        form.addRow("Phone", self.phone_input)
        form.addRow("Email", self.email_input)
        form.addRow("Billing Address", self.billing_address_input)
        form.addRow("Job Address", self.job_address_input)
        form.addRow("Notes", self.notes_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_customer)
        buttons.rejected.connect(self.reject)

        root.addLayout(form)
        root.addWidget(buttons)

        self.name_input.setFocus()

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
            name=name,
            company=self.company_input.text().strip(),
            phone=self.phone_input.text().strip(),
            email=self.email_input.text().strip(),
            billing_address=self.billing_address_input.toPlainText().strip(),
            job_address=self.job_address_input.toPlainText().strip(),
            notes=self.notes_input.toPlainText().strip(),
        )

        self.created_customer = self.repository.create(customer)
        self.accept()
