from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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

from database.service_repository import ServiceRepository
from models.service import Service


class ServicesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboard")

        self.repository = ServiceRepository()
        self.current_service_id: int | None = None

        self.build_ui()
        self.refresh_categories()
        self.load_services()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        header = QHBoxLayout()

        heading_group = QVBoxLayout()
        heading_group.setSpacing(2)

        heading = QLabel("Service Library")
        heading.setObjectName("pageHeading")

        subtitle = QLabel(
            "Save frequently used painting and handyman services."
        )
        subtitle.setObjectName("pageSubtitle")

        heading_group.addWidget(heading)
        heading_group.addWidget(subtitle)

        new_button = QPushButton("+ New Service")
        new_button.setObjectName("primaryButton")
        new_button.setFixedSize(145, 42)
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self.clear_form)

        header.addLayout(heading_group)
        header.addStretch()
        header.addWidget(new_button)

        root.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(16)

        content.addWidget(self.build_list_panel(), 1)
        content.addWidget(self.build_details_panel(), 2)

        root.addLayout(content, 1)

    def build_list_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Saved Services")
        title.setObjectName("panelTitle")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("formInput")
        self.search_input.setPlaceholderText("Search services...")
        self.search_input.textChanged.connect(self.apply_filters)

        self.category_filter = QComboBox()
        self.category_filter.setObjectName("formInput")
        self.category_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.favorites_filter = QCheckBox("Favorites only")
        self.favorites_filter.setObjectName("formCheckBox")
        self.favorites_filter.stateChanged.connect(self.apply_filters)

        self.service_list = QListWidget()
        self.service_list.setObjectName("serviceList")
        self.service_list.itemSelectionChanged.connect(
            self.load_selected_service
        )

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.category_filter)
        layout.addWidget(self.favorites_filter)
        layout.addWidget(self.service_list, 1)

        return panel

    def build_details_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(14)

        title = QLabel("Service Details")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.name_input = QLineEdit()
        self.category_input = QComboBox()
        self.category_input.setEditable(True)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Describe the work included in this service."
        )
        self.description_input.setFixedHeight(145)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 999999.0)
        self.quantity_input.setDecimals(2)
        self.quantity_input.setValue(1.0)

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.0, 99999999.99)
        self.rate_input.setDecimals(2)
        self.rate_input.setPrefix("$")

        self.taxable_input = QCheckBox("Taxable")
        self.favorite_input = QCheckBox("Favorite")
        self.active_input = QCheckBox("Active")
        self.active_input.setChecked(True)

        for widget in (
            self.name_input,
            self.category_input,
            self.description_input,
            self.quantity_input,
            self.rate_input,
        ):
            widget.setObjectName("formInput")

        for widget in (
            self.taxable_input,
            self.favorite_input,
            self.active_input,
        ):
            widget.setObjectName("formCheckBox")

        form.addRow("Service Name *", self.name_input)
        form.addRow("Category", self.category_input)
        form.addRow("Description", self.description_input)
        form.addRow("Default Quantity", self.quantity_input)
        form.addRow("Default Rate", self.rate_input)

        options = QHBoxLayout()
        options.addWidget(self.taxable_input)
        options.addWidget(self.favorite_input)
        options.addWidget(self.active_input)
        options.addStretch()

        form.addRow("Options", options)

        layout.addLayout(form)
        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()

        delete_button = QPushButton("Delete")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self.delete_service)

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("secondaryButton")
        clear_button.clicked.connect(self.clear_form)

        save_button = QPushButton("Save Service")
        save_button.setObjectName("primaryButton")
        save_button.setFixedSize(135, 40)
        save_button.clicked.connect(self.save_service)

        buttons.addWidget(delete_button)
        buttons.addWidget(clear_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        return panel

    def refresh_categories(self) -> None:
        current_filter = (
            self.category_filter.currentText()
            if hasattr(self, "category_filter")
            else ""
        )

        categories = self.repository.get_categories()

        if hasattr(self, "category_filter"):
            self.category_filter.blockSignals(True)
            self.category_filter.clear()
            self.category_filter.addItem("All categories", "")

            for category in categories:
                self.category_filter.addItem(category, category)

            index = self.category_filter.findData(current_filter)
            if index >= 0:
                self.category_filter.setCurrentIndex(index)

            self.category_filter.blockSignals(False)

        if hasattr(self, "category_input"):
            current_entry = self.category_input.currentText()

            self.category_input.clear()
            self.category_input.addItems(categories)
            self.category_input.setEditText(current_entry)

    def load_services(
        self,
        services: list[Service] | None = None,
    ) -> None:
        self.service_list.clear()

        if services is None:
            services = self.repository.get_all()

        for service in services:
            star = "★ " if service.favorite else ""
            inactive = " — Inactive" if not service.active else ""

            text = star + service.name

            if service.category:
                text += f"\n{service.category}"

            text += (
                f"  •  ${service.default_rate_cents / 100:,.2f}"
                f"{inactive}"
            )

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, service.id)
            self.service_list.addItem(item)

    def apply_filters(self, *_args) -> None:
        category = self.category_filter.currentData() or ""

        services = self.repository.search(
            search_text=self.search_input.text(),
            category=category,
            favorites_only=self.favorites_filter.isChecked(),
        )

        self.load_services(services)

    def load_selected_service(self) -> None:
        selected = self.service_list.selectedItems()

        if not selected:
            return

        service_id = selected[0].data(Qt.ItemDataRole.UserRole)
        service = self.repository.get_by_id(service_id)

        if service is None:
            return

        self.current_service_id = service.id
        self.name_input.setText(service.name)
        self.category_input.setEditText(service.category)
        self.description_input.setPlainText(service.description)
        self.quantity_input.setValue(service.default_quantity)
        self.rate_input.setValue(service.default_rate_cents / 100)
        self.taxable_input.setChecked(service.taxable)
        self.favorite_input.setChecked(service.favorite)
        self.active_input.setChecked(service.active)

    def save_service(self) -> None:
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Service Name Required",
                "Enter a name for the service.",
            )
            self.name_input.setFocus()
            return

        service = Service(
            id=self.current_service_id,
            name=name,
            category=self.category_input.currentText().strip(),
            description=self.description_input.toPlainText().strip(),
            default_quantity=self.quantity_input.value(),
            default_rate_cents=round(self.rate_input.value() * 100),
            taxable=self.taxable_input.isChecked(),
            favorite=self.favorite_input.isChecked(),
            active=self.active_input.isChecked(),
        )

        if service.id is None:
            saved_service = self.repository.create(service)
            self.current_service_id = saved_service.id
            message = "Service created successfully."
        else:
            self.repository.update(service)
            message = "Service updated successfully."

        self.refresh_categories()
        self.apply_filters()

        QMessageBox.information(
            self,
            "Service Saved",
            message,
        )

    def delete_service(self) -> None:
        if self.current_service_id is None:
            QMessageBox.information(
                self,
                "No Service Selected",
                "Select a service before deleting.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Service",
            "Are you sure you want to permanently delete this service?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.repository.delete(self.current_service_id)

        self.clear_form()
        self.refresh_categories()
        self.apply_filters()

    def clear_form(self) -> None:
        self.current_service_id = None
        self.service_list.clearSelection()

        self.name_input.clear()
        self.category_input.setEditText("")
        self.description_input.clear()
        self.quantity_input.setValue(1.0)
        self.rate_input.setValue(0.0)
        self.taxable_input.setChecked(False)
        self.favorite_input.setChecked(False)
        self.active_input.setChecked(True)

        self.name_input.setFocus()
