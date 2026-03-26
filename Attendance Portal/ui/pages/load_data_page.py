# ======================
# ui/pages/load_data_page.py
# ======================
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt


def create_load_data_page(window) -> QWidget:
    page = QWidget()
    outer = QVBoxLayout(page)
    outer.setContentsMargins(40, 40, 40, 40)
    outer.setSpacing(0)
    outer.setAlignment(Qt.AlignmentFlag.AlignTop)

    # ── Page header ──────────────────────────────────────────────────────
    header = QLabel("📥  Load Dataset")
    header.setStyleSheet("font-size: 24px; font-weight: 700; margin-bottom: 6px;")
    outer.addWidget(header)

    sub = QLabel("Import holiday calendars, resource mappings, and custom files into the database.")
    sub.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 30px;")
    outer.addWidget(sub)

    # ── Cards row ────────────────────────────────────────────────────────
    cards_row = QHBoxLayout()
    cards_row.setSpacing(20)

    cards = [
        {
            "icon": "🗓️",
            "title": "Holiday Calendar",
            "desc": "Import national / regional holidays from an Excel file to compute accurate working days.",
            "btn_label": "Import Holidays →",
            "accent": "#00c9a7",
            "action": window.load_holidays_to_db,
        },
        {
            "icon": "📋",
            "title": "Resource Mapping",
            "desc": "Upload an employee-to-team mapping spreadsheet. Used to categorise timesheets by team.",
            "btn_label": "Upload Mapping →",
            "accent": "#845ec2",
            "action": lambda: open_resource_popup(window),
        },
        {
            "icon": "🗂️",
            "title": "Custom File",
            "desc": "Load any CSV or Excel file directly into the app for ad-hoc analysis or archiving.",
            "btn_label": "Upload File →",
            "accent": "#f77f00",
            "action": window.handle_custom_file_upload,
        },
    ]

    for card_cfg in cards:
        card = _build_card(card_cfg)
        cards_row.addWidget(card)

    outer.addLayout(cards_row)
    outer.addStretch()
    return page


def _build_card(cfg: dict) -> QFrame:
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.06);
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(28, 28, 28, 28)
    layout.setSpacing(12)

    icon_lbl = QLabel(cfg["icon"])
    icon_lbl.setStyleSheet(f"""
        font-size: 36px;
        background: {cfg['accent']}22;
        border: 1px solid {cfg['accent']}44;
        border-radius: 14px;
        padding: 12px;
    """)
    icon_lbl.setFixedSize(72, 72)
    icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    title = QLabel(cfg["title"])
    title.setStyleSheet("font-size: 16px; font-weight: 700;")

    desc = QLabel(cfg["desc"])
    desc.setWordWrap(True)
    desc.setStyleSheet("font-size: 12px; color: #64748b; line-height: 1.5;")

    btn = QPushButton(cfg["btn_label"])
    btn.setFixedHeight(42)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {cfg['accent']};
            color: #0f1117;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
        }}
        QPushButton:hover {{
            opacity: 0.9;
        }}
    """)
    btn.clicked.connect(cfg["action"])

    layout.addWidget(icon_lbl)
    layout.addWidget(title)
    layout.addWidget(desc)
    layout.addStretch()
    layout.addWidget(btn)
    return card


def open_resource_popup(window) -> None:
    dialog = QDialog(window)
    dialog.setWindowTitle("Upload Resource Mapping")
    dialog.setFixedSize(420, 220)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(16)

    label = QLabel("Select a resource mapping file (.csv or .xlsx)")
    label.setWordWrap(True)
    layout.addWidget(label)

    file_btn = QPushButton("📂  Choose File")
    file_btn.setFixedHeight(42)
    file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    file_btn.clicked.connect(lambda: _choose_resource_file(window, dialog))
    layout.addWidget(file_btn)

    close_btn = QPushButton("Cancel")
    close_btn.setFixedHeight(36)
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)

    dialog.exec()


def _choose_resource_file(window, parent_dialog) -> None:
    file_path, _ = QFileDialog.getOpenFileName(
        window, "Select File", "", "CSV/Excel Files (*.csv *.xlsx *.xls)"
    )
    if not file_path:
        return
    try:
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            from config import RESOURCE_SHEET_NAME
            df = pd.read_excel(file_path, sheet_name=RESOURCE_SHEET_NAME)

        from core.db import add_data_resource_tab
        add_data_resource_tab(window.db_connection, df)
        QMessageBox.information(window, "Success", "✅ Resource mapping uploaded successfully!")
    except Exception as e:
        QMessageBox.critical(window, "Error", f"Failed to import file:\n{str(e)}")
    parent_dialog.close()
