APP_STYLE = """
QWidget {
    font-family: "Segoe UI", "Arial";
    font-size: 14px;
}

QMainWindow,
#dashboard {
    background-color: #f4f7fb;
}

#sidebar {
    background-color: #0b1f3a;
    border: none;
}

#brand {
    color: #ffffff;
    font-size: 27px;
    font-weight: 800;
    letter-spacing: 2px;
}

#brandSubtitle {
    color: #73a7ff;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
}

#navButton,
#navButtonActive {
    border: none;
    border-radius: 7px;
    padding: 12px 14px;
    text-align: left;
    font-weight: 600;
}

#navButton {
    color: #dbe7f7;
    background-color: transparent;
}

#navButton:hover {
    background-color: #132f52;
    color: #ffffff;
}

#navButtonActive {
    color: #ffffff;
    background-color: #1d63d8;
}

#companyName {
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
}

#companyStatus {
    color: #89a0bb;
    font-size: 11px;
}

#pageHeading {
    color: #10233e;
    font-size: 30px;
    font-weight: 800;
}

#pageSubtitle {
    color: #73839a;
    font-size: 14px;
}

#primaryButton {
    background-color: #1769e0;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: 700;
}

#primaryButton:hover {
    background-color: #1158c2;
}

#metricCard,
#panel {
    background-color: #ffffff;
    border: 1px solid #dfe7f1;
    border-radius: 12px;
}

#metricTitle {
    color: #64748b;
    font-size: 13px;
    font-weight: 700;
}

#metricValue {
    color: #10233e;
    font-size: 28px;
    font-weight: 800;
}

#metricSubtitle {
    color: #8a98aa;
    font-size: 12px;
}

#panelTitle {
    color: #10233e;
    font-size: 17px;
    font-weight: 800;
}

#emptyTitle {
    color: #263b57;
    font-size: 18px;
    font-weight: 700;
}

#emptyText {
    color: #7a899c;
    font-size: 13px;
}

#secondaryButton {
    background-color: #e8f0fd;
    color: #155bc2;
    border: 1px solid #bfd3f4;
    border-radius: 7px;
    padding: 10px 14px;
    font-weight: 700;
}

#secondaryButton:hover {
    background-color: #dce9fb;
}

#actionCard {
    background-color: #f8faff;
    border: 1px solid #e4ebf5;
    border-radius: 9px;
}

#actionButton {
    color: #155bc2;
    background-color: transparent;
    border: none;
    text-align: left;
    font-weight: 800;
    padding: 0;
}

#actionButton:hover {
    color: #0d438f;
}

#actionDescription {
    color: #7a899c;
    font-size: 12px;
}

#footer {
    color: #8d9aac;
    font-size: 11px;
}

#formInput {
    background-color: #ffffff;
    color: #10233e;
    border: 1px solid #ccd7e5;
    border-radius: 7px;
    padding: 8px 10px;
}

#formInput:focus {
    border: 2px solid #1769e0;
}

#customerList {
    background-color: #ffffff;
    border: 1px solid #dfe7f1;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

#customerList::item {
    padding: 10px;
    border-bottom: 1px solid #edf1f6;
}

#customerList::item:selected {
    background-color: #e7f0ff;
    color: #104da7;
    border-radius: 6px;
}

#dangerButton {
    background-color: #fff0f0;
    color: #b42318;
    border: 1px solid #f0b8b4;
    border-radius: 7px;
    padding: 10px 14px;
    font-weight: 700;
}

#dangerButton:hover {
    background-color: #ffe3e1;
}


#estimateTable {
    background-color: #ffffff;
    color: #10233e;
    border: 1px solid #dfe7f1;
    border-radius: 8px;
    gridline-color: #e6edf5;
    alternate-background-color: #f8faff;
}

#estimateTable QHeaderView::section {
    background-color: #eef3fa;
    color: #42546c;
    border: none;
    border-bottom: 1px solid #d7e0eb;
    padding: 10px;
    font-weight: 700;
}

#tableInput {
    background-color: #ffffff;
    color: #10233e;
    border: 1px solid #ccd7e5;
    border-radius: 5px;
    padding: 6px;
}

#tableInput:focus {
    border: 2px solid #1769e0;
}

#totalsPanel {
    background-color: #f8faff;
    border: 1px solid #dfe7f1;
    border-radius: 10px;
}

#totalLine {
    color: #42546c;
    font-size: 14px;
    font-weight: 700;
}

#grandTotal {
    color: #10233e;
    font-size: 24px;
    font-weight: 800;
}

#settingsScroll {
    background-color: transparent;
}

#settingsScroll > QWidget > QWidget {
    background-color: transparent;
}

#logoPreview {
    background-color: #f8faff;
    color: #7a899c;
    border: 1px dashed #b8c6d8;
    border-radius: 8px;
}

#serviceSelectionDialog {
    background-color: #f4f7fb;
}

#dialogHeading {
    color: #10233e;
    font-size: 23px;
    font-weight: 800;
}

#dialogResultText {
    color: #73839a;
    font-size: 13px;
    font-weight: 600;
}

#serviceSelectionTable {
    background-color: #ffffff;
    color: #10233e;
    border: 1px solid #dfe7f1;
    border-radius: 8px;
    alternate-background-color: #f8faff;
    outline: none;
}

#serviceSelectionTable QHeaderView::section {
    background-color: #eef3fa;
    color: #42546c;
    border: none;
    border-bottom: 1px solid #d7e0eb;
    padding: 10px;
    font-weight: 700;
}

#serviceSelectionTable::item {
    padding: 8px;
    border-bottom: 1px solid #edf1f6;
}

#serviceSelectionTable::item:selected {
    background-color: #e7f0ff;
    color: #104da7;
}


#serviceList {
    background-color: #ffffff;
    color: #10233e;
    border: 1px solid #dfe7f1;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

#serviceList::item {
    padding: 11px;
    border-bottom: 1px solid #edf1f6;
}

#serviceList::item:selected {
    background-color: #e7f0ff;
    color: #104da7;
    border-radius: 6px;
}

#formCheckBox {
    color: #42546c;
    spacing: 7px;
    font-weight: 600;
}

#formCheckBox::indicator {
    width: 17px;
    height: 17px;
}

"""
