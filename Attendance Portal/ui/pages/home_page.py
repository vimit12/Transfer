# ======================
# ui/pages/home_page.py — Home page: month/year selection, holiday, category, report
# ======================
import os
import itertools
from collections import Counter

import numpy as np
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QPlainTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QSizePolicy, QDialog, QScrollArea
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6 import QtCore

from core.utils import clean_string, coverage_percentage, read_file
from core.db import (
    get_holidays_for_year, fetch_all_resource_mappings,
    add_data_resource_tab, update_user_leave, update_non_complaint_user
)
from core.excel_generator import (
    generate_excel, add_summary_page, non_compliance_resources
)
from core.holiday_importer import import_holidays_from_excel, save_holidays_to_db, year_has_holidays


# ─────────────────────────────────────────────────────────────────────────────
# Page factory
# ─────────────────────────────────────────────────────────────────────────────

def create_home_page(window) -> QWidget:
    """Build and return the Home page widget, wiring all controls to *window*."""
    # Outer wrapper with scroll support
    page = QWidget()
    outer_layout = QVBoxLayout(page)
    outer_layout.setContentsMargins(0, 0, 0, 0)
    outer_layout.setSpacing(0)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(scroll.Shape.NoFrame)
    scroll_content = QWidget()
    main_layout = QVBoxLayout(scroll_content)
    main_layout.setContentsMargins(40, 32, 40, 32)
    main_layout.setSpacing(16)
    scroll.setWidget(scroll_content)
    outer_layout.addWidget(scroll)

    # ── Page header ───────────────────────────────────────────────────────
    header = QLabel("🏠  Generate Report")
    header.setStyleSheet("font-size: 24px; font-weight: 700; margin-bottom: 2px;")
    sub = QLabel("Select a billing period, load holidays & categories, then generate the attendance report.")
    sub.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 8px;")
    main_layout.addWidget(header)
    main_layout.addWidget(sub)

    # ── Month / Year ──────────────────────────────────────────────────────
    year_month_group = QGroupBox("Billing Period")
    date_layout = QHBoxLayout(year_month_group)
    date_layout.setContentsMargins(16, 18, 16, 18)
    date_layout.setSpacing(16)

    window.month_combo = QComboBox()
    window.month_combo.addItems([
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ])
    window.month_combo.setFixedHeight(38)

    window.year_combo = QComboBox()
    current_year = QDate.currentDate().year()
    window.year_combo.addItems([str(y) for y in range(2022, 2051)])
    window.year_combo.setFixedHeight(38)

    current_month = QDate.currentDate().month()
    window.month_combo.setCurrentIndex(current_month - 1)
    window.year_combo.setCurrentText(str(current_year))

    def update_month_combo():
        selected_year = int(window.year_combo.currentText())
        is_current_year = selected_year == current_year
        if is_current_year:
            window.month_combo.setCurrentIndex(current_month - 1)
        for idx in range(window.month_combo.count()):
            enabled = (idx + 1) <= current_month if is_current_year else True
            window.month_combo.model().item(idx).setEnabled(enabled)

    for idx in range(window.year_combo.count()):
        year_val = int(window.year_combo.itemText(idx))
        window.year_combo.model().item(idx).setEnabled(year_val <= current_year)

    window.year_combo.currentTextChanged.connect(update_month_combo)
    update_month_combo()

    date_layout.addWidget(QLabel("Month:"))
    date_layout.addWidget(window.month_combo, 3)
    date_layout.addSpacing(10)
    date_layout.addWidget(QLabel("Year:"))
    date_layout.addWidget(window.year_combo, 1)
    date_layout.addStretch()

    # ── Holiday Management ────────────────────────────────────────────────
    holiday_group = QGroupBox("Holiday Calendar")
    holiday_layout = QVBoxLayout(holiday_group)
    holiday_layout.setContentsMargins(16, 18, 16, 14)
    holiday_layout.setSpacing(10)

    input_row = QHBoxLayout()
    input_row.setSpacing(10)

    window.holiday_input = QPlainTextEdit()
    window.holiday_input.setFixedHeight(38)
    window.holiday_input.setReadOnly(True)
    window.holiday_input.setPlaceholderText("No holiday file loaded…")
    window.holiday_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    window.load_holiday_btn = QPushButton("📂")
    window.load_holiday_btn.setToolTip("Upload Holiday Excel File")
    window.load_holiday_btn.setFixedSize(38, 38)
    window.load_holiday_btn.setObjectName("load_holiday_btn")
    window.load_holiday_btn.setCursor(Qt.CursorShape.PointingHandCursor)

    window.view_holiday_btn = QPushButton("👁 View")
    window.view_holiday_btn.setFixedHeight(38)
    window.view_holiday_btn.setObjectName("view_holiday_btn")
    window.view_holiday_btn.setCursor(Qt.CursorShape.PointingHandCursor)

    window.format_info_btn = QPushButton("📄 Format")
    window.format_info_btn.setToolTip("Holiday Excel Format Guide")
    window.format_info_btn.setFixedHeight(38)
    window.format_info_btn.setObjectName("format_info_btn")
    window.format_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)

    input_row.addWidget(window.holiday_input)
    input_row.addWidget(window.load_holiday_btn)
    input_row.addWidget(window.view_holiday_btn)
    input_row.addWidget(window.format_info_btn)

    window.format_info_btn.clicked.connect(lambda: show_format_guide(window))
    window.load_holiday_btn.clicked.connect(lambda: load_holidays_to_db(window))
    window.view_holiday_btn.clicked.connect(lambda: show_holiday_viewer(window))

    window.holiday_error_label = QLabel()
    window.holiday_error_label.setStyleSheet("color:#fb7185; font-size:11px;")
    window.holiday_error_label.setWordWrap(True)

    holiday_layout.addLayout(input_row)
    holiday_layout.addWidget(window.holiday_error_label)

    # ── Category ──────────────────────────────────────────────────────────
    category_group = QGroupBox("Resource Category Mapping")
    category_layout = QVBoxLayout(category_group)
    category_layout.setContentsMargins(16, 18, 16, 14)
    category_layout.setSpacing(10)

    cat_input_row = QHBoxLayout()
    cat_input_row.setSpacing(10)

    window.category_input = QPlainTextEdit()
    window.category_input.setFixedHeight(38)
    window.category_input.setReadOnly(True)
    window.category_input.setPlaceholderText("No category file loaded…")
    window.category_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    window.category_btn = QPushButton("📂")
    window.category_btn.setToolTip("Upload Category Excel File")
    window.category_btn.setFixedSize(38, 38)
    window.category_btn.setObjectName("category_btn")
    window.category_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    window.category_btn.clicked.connect(lambda: select_category(window))

    cat_input_row.addWidget(window.category_input)
    cat_input_row.addWidget(window.category_btn)
    category_layout.addLayout(cat_input_row)

    # ── Main file input ───────────────────────────────────────────────────
    groupBox = QGroupBox("Raw Attendance File")
    group_layout = QVBoxLayout(groupBox)
    group_layout.setContentsMargins(16, 18, 16, 14)
    group_layout.setSpacing(10)

    main_input_row = QHBoxLayout()
    main_input_row.setSpacing(10)

    window.main_input = QPlainTextEdit()
    window.main_input.setFixedHeight(38)
    window.main_input.setReadOnly(True)
    window.main_input.setPlaceholderText("No attendance file loaded…")
    window.main_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    window.upload_button = QPushButton("📂 Upload")
    window.upload_button.setToolTip("Select raw attendance Excel file")
    window.upload_button.setObjectName("upload_button")
    window.upload_button.setFixedHeight(38)
    window.upload_button.setCursor(Qt.CursorShape.PointingHandCursor)
    window.upload_button.clicked.connect(lambda: upload_file(window))

    main_input_row.addWidget(window.main_input)
    main_input_row.addWidget(window.upload_button)
    group_layout.addLayout(main_input_row)

    # ── Progress bar ──────────────────────────────────────────────────────
    window.progress_bar = QProgressBar()
    window.progress_bar.setValue(0)
    window.progress_bar.setTextVisible(False)
    window.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    window.progress_bar.setFixedHeight(8)

    # ── Status message ────────────────────────────────────────────────────
    window.msg_label = QLabel()
    window.msg_label.setObjectName("statusMsg")
    window.msg_label.setWordWrap(True)
    window.msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    window.msg_label.hide()

    # ── Generate button ───────────────────────────────────────────────────
    generate_container = QHBoxLayout()
    generate_container.addStretch()
    window.generate_button = QPushButton("⚡  Generate Report")
    window.generate_button.setObjectName("generate_button")
    window.generate_button.setFixedSize(280, 48)
    window.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
    window.generate_button.clicked.connect(lambda: generate_report(window))
    generate_container.addWidget(window.generate_button)
    generate_container.addStretch()

    # ── Assemble ──────────────────────────────────────────────────────────
    main_layout.addWidget(year_month_group)
    main_layout.addWidget(holiday_group)
    main_layout.addWidget(category_group)
    main_layout.addWidget(groupBox)
    main_layout.addWidget(window.progress_bar)
    main_layout.addWidget(window.msg_label)
    main_layout.addSpacing(8)
    main_layout.addLayout(generate_container)
    main_layout.addStretch()

    return page


# ─────────────────────────────────────────────────────────────────────────────
# Actions
# ─────────────────────────────────────────────────────────────────────────────

def show_message(window, text: str, msg_type: str = "info", timeout: int = 5000):
    window.msg_label.setProperty("messageType", msg_type)
    window.msg_label.setText(text)
    window.msg_label.style().polish(window.msg_label)
    window.msg_label.setFixedHeight(window.msg_label.sizeHint().height())
    window.msg_label.show()
    if timeout > 0:
        QTimer.singleShot(timeout, lambda: _clear_message(window))


def _clear_message(window):
    window.msg_label.hide()
    window.msg_label.setText("")


def load_holidays_to_db(window):
    file_path, _ = QFileDialog.getOpenFileName(
        window, "Select Holiday File", "",
        "Spreadsheet Files (*.xlsx *.xls *.numbers);;All Files (*)"
    )
    if not file_path:
        return
    try:
        file_name = os.path.basename(file_path)
        file_size_kb = os.path.getsize(file_path) / 1024.0
        window.holiday_input.setPlainText(f"{file_name} ({file_size_kb:.1f} KB)")

        excel_year, holidays = import_holidays_from_excel(file_path)

        if year_has_holidays(window.db_connection, excel_year):
            confirm = QMessageBox.question(
                window, "Override Confirmation",
                f"Holidays for {excel_year} already exist. Override?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

        save_holidays_to_db(window.db_connection, excel_year, holidays)
        show_message(window, f"✅ Imported {len(holidays)} holidays for {excel_year}", "success", 4000)
    except Exception as e:
        show_message(window, f"Error: {str(e)}", "error", 6000)


def show_holiday_viewer(window):
    year = window.year_combo.currentText()
    holidays = get_holidays_for_year(window.db_connection, year)
    if not holidays:
        QMessageBox.information(window, "No Holidays", f"No holidays found for {year}.")
        return
    dialog = QDialog(window)
    dialog.setWindowTitle(f"Holidays for {year}")
    dialog.resize(400, 400)
    layout = QVBoxLayout(dialog)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    content = QWidget()
    content_layout = QVBoxLayout(content)
    for h in sorted(holidays):
        content_layout.addWidget(QLabel(h))
    content_layout.addStretch()
    scroll.setWidget(content)
    layout.addWidget(scroll)
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    dialog.exec()


def show_format_guide(window):
    guide_text = """<html><body>
        <h2>Holiday Excel Format</h2>
        <ol>
            <li>First cell (A1) must contain the 4-digit year (e.g., <b>2025</b>).</li>
            <li>Subsequent rows: one date per cell in any valid Excel date format.</li>
            <li>All dates must belong to the specified year.</li>
        </ol>
        <table border="1" cellpadding="6" style="border-collapse:collapse">
            <tr><th>Year</th></tr>
            <tr><td>DD-MM-YYYY</td></tr>
            <tr><td>DD-MM-YYYY</td></tr>
            <tr><td>etc ...</td></tr>
        </table>
    </body></html>"""
    msg = QMessageBox(window)
    msg.setWindowTitle("Format Guide")
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setText(guide_text)
    msg.exec()


def select_category(window):
    filepath, _ = QFileDialog.getOpenFileName(
        window, "Open Excel File", "", "Excel Files (*.xlsx *.xls, *.csv)"
    )
    window.raw_category_list, window.name_order_list = [], []
    window.categories, window.name_mapping = {}, {}

    try:
        if not filepath:
            return
        from config import RESOURCE_SHEET_NAME
        fileInfo = QtCore.QFileInfo(filepath)
        file_name = fileInfo.fileName()
        file_size_kb = fileInfo.size() / 1024.0
        window.category_input.setPlainText(f"{file_name} ({file_size_kb:.2f} KB)")

        df = pd.read_excel(filepath, sheet_name=RESOURCE_SHEET_NAME)
        df.replace({np.nan: None}, inplace=True)
        add_data_resource_tab(window.db_connection, df)
        window.raw_category_list = df.to_dict(orient="records")

        for item in window.raw_category_list:
            name = clean_string(item['Full Name'])
            team = item["Team"]
            window.categories.setdefault(team, []).append(name)
            window.name_mapping[name] = [
                item["521 ID"], item["Point of Contact"],
                item["Start Date"], item["End Date"]
            ]

        for k, v in window.categories.items():
            temp = sorted(v)
            window.categories[k] = temp
            window.name_order_list.extend(temp)

        show_message(window, "Category data successfully created!", "success", 3000)
    except Exception as e:
        window.raw_category_list, window.name_order_list = [], []
        window.categories, window.name_mapping = {}, {}
        window.category_input.setPlainText("")
        show_message(window, "Error: Not a valid category file", "error", 5000)


def upload_file(window):
    file_dialog = QFileDialog(window)
    filepath, _ = file_dialog.getOpenFileName(window, "Open Excel File", "", "Excel Files (*.xlsx *.xls, *.csv)")
    if filepath:
        fileInfo = QtCore.QFileInfo(filepath)
        file_name = fileInfo.fileName()
        file_size_kb = fileInfo.size() / 1024.0
        window.main_input.setPlainText(f"{file_name} ({file_size_kb:.2f} KB)")
        window.df = read_file(filepath)
        try:
            dict_value = dict(Counter(list(itertools.chain.from_iterable(
                [[item.split("-")[-1] for item in j] for j in [list(i.keys())[4:-2] for i in window.df]]
            ))))
            value = max(dict_value, key=dict_value.get)
            selected_month = window.month_combo.currentText()
            if value == selected_month[:3]:
                show_message(window, "Valid Raw Excel Loaded", "info", 4000)
            else:
                show_message(window, "Invalid Raw excel, please check the file or selected month.", "error", 5000)
                window.main_input.setPlainText("")
                window.df = None
        except Exception as e:
            show_message(window, "Invalid Raw excel, please check the file.", "error", 5000)
            window.df = None


def generate_report(window):
    if not all([window.raw_category_list, window.categories, window.name_mapping, window.name_order_list]):
        raw_list, cats, name_map, name_order = fetch_all_resource_mappings(window.db_connection)
        if not raw_list:
            show_message(window, "Error: Please select proper category file!", "error", 5000)
            return
        window.raw_category_list = raw_list
        window.categories = cats
        window.name_mapping = name_map
        window.name_order_list = name_order

    window.selected_month = window.month_combo.currentText()
    window.selected_year = window.year_combo.currentText()
    window.HOLIDAY_LIST = get_holidays_for_year(window.db_connection, window.selected_year)

    if not window.HOLIDAY_LIST:
        show_message(window, f"Error: Please load the holiday for year {window.selected_year}.", "error", 5000)
        return

    if window.df:
        # Clean newlines from column keys
        cleaned_df = []
        for data_dict in window.df:
            cleaned_df.append({k.replace("\n", " ").strip(): v for k, v in data_dict.items()})
        window.df = cleaned_df

        for category, valid_rsnames in window.categories.items():
            file_name = f"{category}_Timesheet_{window.selected_month} {window.selected_year}.xlsx"
            filtered_df = [
                record for record in window.df
                if any(coverage_percentage(clean_string(record["Rsname"]), clean_string(vr)) >= 60
                       for vr in valid_rsnames)
            ]
            if not filtered_df:
                print(f"No Data for the category - {category}")
                continue

            status, response, user_data, non_comp, user_leave = generate_excel(
                window.selected_month, window.selected_year, file_name,
                filtered_df, window.HOLIDAY_LIST, window.name_mapping,
                window.name_order_list, window.progress_bar
            )

            if status == 200:
                remaining = 100 - window.progress_bar.value()
                step = remaining / 3
                add_summary_page(user_data, file_name)
                window.progress_bar.setValue(window.progress_bar.value() + int(step * 2))
            else:
                show_message(window, f"Error: {response}", "error", 5000)

            if non_comp:
                non_compliance_resources(
                    non_comp,
                    f"{category}_non_complaint_{window.selected_month} {window.selected_year}.xlsx"
                )
                update_non_complaint_user(window.db_connection, non_comp)

            if user_leave:
                update_user_leave(window.db_connection, user_leave)

        show_message(window, "Report Generated Successfully!", "success", 10000)
        window.progress_bar.setValue(100)
    else:
        show_message(window, "Error: Please provide raw Excel file as input.", "error", 5000)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _group_style() -> str:
    """Legacy — kept for compat but the theme CSS handles group boxes now."""
    return ""
