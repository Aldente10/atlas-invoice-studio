from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, subtitle: str) -> None:
        super().__init__()

        self.setObjectName("metricCard")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setMinimumHeight(125)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("metricTitle")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("metricSubtitle")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("dashboard")
        self.build_ui()

    def build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()

        heading_group = QVBoxLayout()
        heading_group.setSpacing(2)

        heading = QLabel("Dashboard")
        heading.setObjectName("pageHeading")

        greeting = QLabel("Welcome to Atlas Invoice Studio")
        greeting.setObjectName("pageSubtitle")

        heading_group.addWidget(heading)
        heading_group.addWidget(greeting)

        new_button = QPushButton("+  New")
        new_button.setObjectName("primaryButton")
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.setFixedSize(120, 42)

        header_layout.addLayout(heading_group)
        header_layout.addStretch()
        header_layout.addWidget(new_button)

        layout.addLayout(header_layout)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)

        metrics_layout.addWidget(
            MetricCard("Open Estimates", "0", "$0.00 awaiting approval")
        )
        metrics_layout.addWidget(
            MetricCard("Unpaid Invoices", "0", "$0.00 outstanding")
        )
        metrics_layout.addWidget(
            MetricCard("Paid This Month", "$0.00", "No payments recorded")
        )
        metrics_layout.addWidget(
            MetricCard("Customers", "0", "Ready for the first customer")
        )

        layout.addLayout(metrics_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        content_layout.addWidget(self.build_recent_documents_panel(), 2)
        content_layout.addWidget(self.build_quick_actions_panel(), 1)

        layout.addLayout(content_layout, 1)

        footer = QLabel("Atlas Invoice Studio  •  Version 0.1.0")
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

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(empty_title)
        layout.addWidget(empty_text)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(create_button)
        button_row.addStretch()

        layout.addLayout(button_row)
        layout.addStretch()

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
            ("New Estimate", "Create a professional customer estimate"),
            ("New Invoice", "Create an invoice directly"),
            ("Add Customer", "Save customer and job information"),
            ("Company Settings", "Logo, contact details and defaults"),
        ]

        for button_text, description in actions:
            card = QFrame()
            card.setObjectName("actionCard")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(4)

            button = QPushButton(button_text)
            button.setObjectName("actionButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            description_label = QLabel(description)
            description_label.setObjectName("actionDescription")
            description_label.setWordWrap(True)

            card_layout.addWidget(button)
            card_layout.addWidget(description_label)

            layout.addWidget(card)

        layout.addStretch()

        return panel
