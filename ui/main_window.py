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

from theme.styles import APP_STYLE
from ui.dashboard_page import DashboardPage


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

        message = QLabel(f"{title} workspace is ready for development.")
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

        self.setWindowTitle("Atlas Invoice Studio")
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
        self.page_stack.addWidget(DashboardPage())
        self.page_stack.addWidget(
            PlaceholderPage(
                "Customers",
                "Manage customer contact information and job locations.",
            )
        )
        self.page_stack.addWidget(
            PlaceholderPage(
                "Estimates",
                "Create, review, and manage customer estimates.",
            )
        )
        self.page_stack.addWidget(
            PlaceholderPage(
                "Invoices",
                "Create invoices and track outstanding balances.",
            )
        )
        self.page_stack.addWidget(
            PlaceholderPage(
                "Products & Services",
                "Maintain reusable labor, service, and material items.",
            )
        )
        self.page_stack.addWidget(
            PlaceholderPage(
                "Reports",
                "Review sales, outstanding balances, and document activity.",
            )
        )
        self.page_stack.addWidget(
            PlaceholderPage(
                "Settings",
                "Configure company branding, numbering, and document defaults.",
            )
        )

    def build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(225)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(8)

        brand = QLabel("ATLAS")
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
            "Products & Services",
            "Reports",
            "Settings",
        ]

        for page_index, text in enumerate(navigation_items):
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, index=page_index: self.show_page(index)
            )

            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()

        company = QLabel("PALM COAST PROS")
        company.setObjectName("companyName")

        status = QLabel("Local desktop edition")
        status.setObjectName("companyStatus")

        layout.addWidget(company)
        layout.addWidget(status)

        return sidebar

    def show_page(self, index: int) -> None:
        self.page_stack.setCurrentIndex(index)

        for button_index, button in enumerate(self.nav_buttons):
            if button_index == index:
                button.setObjectName("navButtonActive")
            else:
                button.setObjectName("navButton")

            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
