from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from database.service_repository import ServiceRepository
from models.service import Service


class ServiceSelectionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.repository = ServiceRepository()
        self.selected_service: Service | None = None

        self.setObjectName("serviceSelectionDialog")
        self.setWindowTitle("Add Service")
        self.resize(720, 560)
        self.setMinimumSize(620, 480)

        self.build_ui()
        self.load_categories()
        self.load_services()

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        heading = QLabel("Add Service")
        heading.setObjectName("dialogHeading")

        subtitle = QLabel(
            "Choose a saved painting or handyman service to add "
            "to the estimate."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)

        root.addWidget(heading)
        root.addWidget(subtitle)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("formInput")
        self.search_input.setPlaceholderText("Search services...")
        self.search_input.textChanged.connect(self.apply_filters)

        self.category_filter = QComboBox()
        self.category_filter.setObjectName("formInput")
        self.category_filter.setMinimumWidth(170)
        self.category_filter.currentIndexChanged.connect(
            self.apply_filters
        )

        self.favorites_filter = QCheckBox("Favorites only")
        self.favorites_filter.setObjectName("formCheckBox")
        self.favorites_filter.stateChanged.connect(self.apply_filters)

        filters.addWidget(self.search_input, 1)
        filters.addWidget(self.category_filter)
        filters.addWidget(self.favorites_filter)

        root.addLayout(filters)

        self.result_label = QLabel("")
        self.result_label.setObjectName("dialogResultText")
        root.addWidget(self.result_label)

        self.service_list = QListWidget()
        self.service_list.setObjectName("serviceSelectionList")
        self.service_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection
        )
        self.service_list.itemDoubleClicked.connect(
            self.accept_selected_service
        )

        root.addWidget(self.service_list, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(self.reject)

        add_button = QPushButton("Add Selected Service")
        add_button.setObjectName("primaryButton")
        add_button.setMinimumSize(175, 42)
        add_button.clicked.connect(self.accept_selected_service)

        buttons.addWidget(cancel_button)
        buttons.addWidget(add_button)

        root.addLayout(buttons)

    def load_categories(self) -> None:
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("All categories", "")

        for category in self.repository.get_categories():
            self.category_filter.addItem(category, category)

        self.category_filter.blockSignals(False)

    def load_services(
        self,
        services: list[Service] | None = None,
    ) -> None:
        self.service_list.clear()

        if services is None:
            services = self.repository.get_all(active_only=True)

        for service in services:
            favorite = "★ " if service.favorite else ""
            category = service.category or "Uncategorized"
            quantity = f"{service.default_quantity:g}"
            rate = service.default_rate_cents / 100

            display = (
                f"{favorite}{service.name}\n"
                f"{category}  •  Qty {quantity}  •  ${rate:,.2f}"
            )

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, service.id)
            item.setToolTip(service.description)
            self.service_list.addItem(item)

        count = self.service_list.count()
        self.result_label.setText(
            f"{count} service{'s' if count != 1 else ''} found"
        )

        if count > 0:
            self.service_list.setCurrentRow(0)

    def apply_filters(self, *_args) -> None:
        category = self.category_filter.currentData() or ""

        services = self.repository.search(
            search_text=self.search_input.text(),
            category=category,
            favorites_only=self.favorites_filter.isChecked(),
            active_only=True,
        )

        self.load_services(services)

    def accept_selected_service(self, *_args) -> None:
        selected_items = self.service_list.selectedItems()

        if not selected_items:
            return

        service_id = selected_items[0].data(
            Qt.ItemDataRole.UserRole
        )

        service = self.repository.get_by_id(service_id)

        if service is None or not service.active:
            return

        self.selected_service = service
        self.accept()
