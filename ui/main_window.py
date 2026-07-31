from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from release_metadata import PRODUCT_NAME, PUBLISHER, VERSION
from theme.styles import APP_STYLE
from ui.customers_page import CustomersPage
from ui.dashboard_page import DashboardPage
from ui.estimates_page import EstimatesPage
from ui.invoices_page import InvoicesPage
from ui.settings_page import SettingsPage
from ui.services_page import ServicesPage


class PlaceholderPage(QWidget):
    def __init__(self, title: str, subtitle: str) -> None:
        super().__init__()
        self.setObjectName("dashboard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)

        heading = QLabel(title)
        heading.setObjectName("pageHeading")

        description = QLabel(subtitle)
        description.setObjectName("pageSubtitle")

        panel = QFrame()
        panel.setObjectName("panel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)

        message = QLabel("Coming Soon — reports are not included in this beta.")
        message.setObjectName("emptyTitle")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel_layout.addStretch()
        panel_layout.addWidget(message)
        panel_layout.addStretch()

        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addSpacing(12)
        layout.addWidget(panel, 1)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(f"{PRODUCT_NAME} {VERSION}")
        self.resize(1280, 760)
        self.setMinimumSize(1050, 650)

        self.nav_buttons: list[QPushButton] = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.page_stack = QStackedWidget()
        self.build_pages()

        root_layout.addWidget(self.build_sidebar())
        root_layout.addWidget(self.page_stack, 1)

        self.setStyleSheet(APP_STYLE)
        self.show_page(0)

    def build_pages(self) -> None:
        self.dashboard_page = DashboardPage()
        self.customers_page = CustomersPage()
        self.estimates_page = EstimatesPage()
        self.invoices_page = InvoicesPage()

        self.dashboard_page.new_estimate_requested.connect(self.new_estimate)
        self.dashboard_page.new_invoice_requested.connect(self.new_invoice)
        self.dashboard_page.add_customer_requested.connect(self.add_customer)
        self.dashboard_page.settings_requested.connect(lambda: self.show_page(6))
        self.dashboard_page.estimate_requested.connect(self.open_estimate)
        self.dashboard_page.invoice_requested.connect(self.open_invoice)
        self.customers_page.data_changed.connect(self.dashboard_page.refresh)
        self.estimates_page.data_changed.connect(self.dashboard_page.refresh)
        self.invoices_page.data_changed.connect(self.dashboard_page.refresh)
        self.estimates_page.invoice_created.connect(self.open_invoice)

        self.page_stack.addWidget(self.dashboard_page)
        self.page_stack.addWidget(self.customers_page)
        self.page_stack.addWidget(self.estimates_page)
        self.page_stack.addWidget(self.invoices_page)
        self.page_stack.addWidget(ServicesPage())
        self.page_stack.addWidget(
            PlaceholderPage(
                "Reports — Coming Soon",
                "Reports are planned for a future release.",
            )
        )
        self.settings_page = SettingsPage()
        self.settings_page.settings_saved.connect(self.update_company_name)
        self.page_stack.addWidget(self.settings_page)

    def build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(8)

        brand = QLabel(PUBLISHER.upper())
        brand.setObjectName("brand")

        subtitle = QLabel("INVOICE STUDIO")
        subtitle.setObjectName("brandSubtitle")

        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        navigation_items = [
            "Dashboard",
            "Customers",
            "Estimates",
            "Invoices",
            "Service Library",
            "Reports (Coming Soon)",
            "Settings",
        ]

        for page_index, text in enumerate(navigation_items):
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, index=page_index: self.show_page(index)
            )

            if page_index == 5:
                button.setEnabled(False)
                button.setToolTip("Reports are coming in a future release.")

            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()

        self.company_label = QLabel(
            self.settings_page.settings_repository.get().business_name.upper()
            or "YOUR COMPANY"
        )
        self.company_label.setObjectName("companyName")

        status = QLabel(f"Local desktop beta • {VERSION}")
        status.setObjectName("companyStatus")

        layout.addWidget(self.company_label)
        layout.addWidget(status)

        return sidebar

    def show_page(self, index: int) -> None:
        if index == 0:
            self.dashboard_page.refresh()
        if index == 3:
            self.invoices_page.load_saved_invoices()
        if index == 6:
            self.settings_page.load_settings()
        self.page_stack.setCurrentIndex(index)

        for button_index, button in enumerate(self.nav_buttons):
            button.setObjectName(
                "navButtonActive" if button_index == index else "navButton"
            )
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def open_invoice(self, invoice_id: int) -> None:
        self.invoices_page.load_saved_invoices()
        self.invoices_page.open_invoice(invoice_id)
        self.show_page(3)

    def open_estimate(self, estimate_id: int) -> None:
        self.estimates_page.open_estimate(estimate_id)
        self.show_page(2)

    def new_estimate(self) -> None:
        self.estimates_page.start_new_estimate()
        self.show_page(2)

    def new_invoice(self) -> None:
        self.invoices_page.start_new_invoice()
        self.show_page(3)

    def add_customer(self) -> None:
        self.customers_page.clear_form()
        self.show_page(1)

    def update_company_name(self, business_name: str) -> None:
        self.company_label.setText(business_name.upper() or "YOUR COMPANY")
