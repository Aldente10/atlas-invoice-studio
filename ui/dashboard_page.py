from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database.dashboard_repository import DashboardRepository, RecentDocument
from release_metadata import PRODUCT_NAME, display_version


class MetricCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(125)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("metricTitle")
        self.value_label = QLabel()
        self.value_label.setObjectName("metricValue")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("metricSubtitle")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch()

    def set_metric(self, value: str, subtitle: str) -> None:
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)


class DashboardPage(QWidget):
    new_estimate_requested = Signal()
    new_invoice_requested = Signal()
    add_customer_requested = Signal()
    settings_requested = Signal()
    estimate_requested = Signal(int)
    invoice_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dashboard")
        self.repository = DashboardRepository()
        self.build_ui()
        self.refresh()

    def build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        heading_group = QVBoxLayout()
        heading_group.setSpacing(2)
        heading = QLabel("Dashboard")
        heading.setObjectName("pageHeading")
        greeting = QLabel(f"Welcome to {PRODUCT_NAME}")
        greeting.setObjectName("pageSubtitle")
        heading_group.addWidget(heading)
        heading_group.addWidget(greeting)

        new_button = QPushButton("+ New Estimate")
        new_button.setObjectName("primaryButton")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.setFixedSize(145, 42)
        new_button.clicked.connect(self.new_estimate_requested.emit)

        header_layout.addLayout(heading_group)
        header_layout.addStretch()
        header_layout.addWidget(new_button)
        layout.addLayout(header_layout)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)
        self.open_estimates_card = MetricCard("Open Estimates")
        self.unpaid_invoices_card = MetricCard("Unpaid Invoices")
        self.paid_month_card = MetricCard("Paid This Month")
        self.customers_card = MetricCard("Customers")
        metrics_layout.addWidget(self.open_estimates_card)
        metrics_layout.addWidget(self.unpaid_invoices_card)
        metrics_layout.addWidget(self.paid_month_card)
        metrics_layout.addWidget(self.customers_card)
        layout.addLayout(metrics_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        content_layout.addWidget(self.build_recent_documents_panel(), 2)
        content_layout.addWidget(self.build_quick_actions_panel(), 1)
        layout.addLayout(content_layout, 1)

        footer = QLabel(display_version())
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(footer)

    def build_recent_documents_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)
        title = QLabel("Recent Documents")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.recent_stack = QStackedWidget()
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("customerList")
        self.recent_list.setToolTip("Double-click a document to open it.")
        self.recent_list.itemDoubleClicked.connect(self._open_recent_document)
        self.recent_stack.addWidget(self.recent_list)

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_title = QLabel("No estimates or invoices yet")
        empty_title.setObjectName("emptyTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text = QLabel(
            "Create the first estimate and it will appear here for quick access."
        )
        empty_text.setObjectName("emptyText")
        empty_text.setWordWrap(True)
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        create_button = QPushButton("Create First Estimate")
        create_button.setObjectName("secondaryButton")
        create_button.setCursor(Qt.CursorShape.PointingHandCursor)
        create_button.setFixedWidth(190)
        create_button.clicked.connect(self.new_estimate_requested.emit)
        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(create_button)
        button_row.addStretch()
        empty_layout.addStretch()
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_text)
        empty_layout.addLayout(button_row)
        empty_layout.addStretch()
        self.recent_stack.addWidget(empty_widget)
        layout.addWidget(self.recent_stack, 1)
        return panel

    def build_quick_actions_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        title = QLabel("Quick Actions")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        actions = [
            (
                "New Estimate",
                "Create a professional customer estimate",
                self.new_estimate_requested,
            ),
            ("New Invoice", "Create an invoice directly", self.new_invoice_requested),
            (
                "Add Customer",
                "Save customer and job information",
                self.add_customer_requested,
            ),
            (
                "Company Settings",
                "Logo, contact details and defaults",
                self.settings_requested,
            ),
        ]
        for button_text, description, signal in actions:
            card = QFrame()
            card.setObjectName("actionCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(4)
            button = QPushButton(button_text)
            button.setObjectName("actionButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(signal.emit)
            description_label = QLabel(description)
            description_label.setObjectName("actionDescription")
            description_label.setWordWrap(True)
            card_layout.addWidget(button)
            card_layout.addWidget(description_label)
            layout.addWidget(card)
        layout.addStretch()
        return panel

    def refresh(self) -> None:
        summary = self.repository.get_summary()
        self.open_estimates_card.set_metric(
            str(summary.open_estimate_count),
            f"{self._currency(summary.open_estimate_total_cents)} awaiting approval",
        )
        self.unpaid_invoices_card.set_metric(
            str(summary.unpaid_invoice_count),
            f"{self._currency(summary.unpaid_invoice_total_cents)} outstanding",
        )
        self.paid_month_card.set_metric(
            self._currency(summary.paid_this_month_total_cents),
            "Invoices dated this month and marked paid",
        )
        customer_text = "customer" if summary.customer_count == 1 else "customers"
        self.customers_card.set_metric(
            str(summary.customer_count),
            f"{summary.customer_count} saved {customer_text}",
        )
        self._load_recent_documents(self.repository.get_recent_documents())

    def _load_recent_documents(self, documents: list[RecentDocument]) -> None:
        self.recent_list.clear()
        for document in documents:
            customer = document.customer_name
            if document.customer_company:
                customer += f" — {document.customer_company}"
            text = (
                f"{document.document_type} #{document.document_number}  •  {customer}\n"
                f"{document.document_date}  •  {document.status}  •  "
                f"{self._currency(document.total_cents)}"
            )
            item = QListWidgetItem(text)
            item.setData(
                Qt.ItemDataRole.UserRole,
                (document.document_type, document.document_id),
            )
            self.recent_list.addItem(item)
        self.recent_stack.setCurrentIndex(0 if documents else 1)

    def _open_recent_document(self, item: QListWidgetItem) -> None:
        document_type, document_id = item.data(Qt.ItemDataRole.UserRole)
        if document_type == "Estimate":
            self.estimate_requested.emit(document_id)
        else:
            self.invoice_requested.emit(document_id)

    @staticmethod
    def _currency(cents: int) -> str:
        return f"${cents / 100:,.2f}"
