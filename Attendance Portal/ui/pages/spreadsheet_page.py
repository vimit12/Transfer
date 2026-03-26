# ======================
# ui/pages/spreadsheet_page.py — Load Spreadsheet + Analyze
# ======================
import re
import json
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QGroupBox,
    QComboBox, QTextEdit, QFrame, QScrollArea, QGridLayout, QLineEdit,
    QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtGui import QFont, QIcon, QColor
from PyQt6.QtCore import Qt

from core.utils import coverage_percentage
from core.db import save_mapping, create_dynamic_table
from dashboard.dash_app import show_dashboard


_BUTTON_STYLE = """
    QPushButton {
        background-color: #ffffff; border: 2px solid #d0d0d0;
        border-radius: 16px; font-size: 14pt; font-weight: 500;
        padding: 10px 20px; color: #333;
    }
    QPushButton:hover  { background-color: #f2f9ff; border: 2px solid #7cbfff; color: #005999; }
    QPushButton:pressed { background-color: #e6f0ff; border: 2px solid #5aa0ff; }
"""
_REQUIRED_COLS = {'Number', 'Opened By', 'Leave Type', 'Start Date', 'End Date', 'Status', 'Created'}


def create_spreadsheet_page(window) -> QWidget:
    page = QWidget()
    outer_layout = QVBoxLayout(page)
    outer_layout.setContentsMargins(20, 20, 20, 20)
    outer_layout.setSpacing(20)

    # Header
    header_layout = QHBoxLayout()
    title = QLabel("📊 Spreadsheet Loader")
    title.setStyleSheet("font-size: 18px; font-weight: bold;")
    title.setAlignment(Qt.AlignmentFlag.AlignLeft)

    window.load_data_card = QPushButton("📂 Load Excel/CSV File")
    window.load_data_card.setStyleSheet(_BUTTON_STYLE)
    window.load_data_card.clicked.connect(lambda: handle_custom_file_upload(window))

    window.analyze_button = QPushButton("📊 Analyze")
    window.analyze_button.setEnabled(False)
    window.analyze_button.setStyleSheet(_BUTTON_STYLE + "QPushButton { background-color:#bdc3c7; color:#7f8c8d; }")
    window.analyze_button.clicked.connect(lambda: handle_analysis(window))

    window.save_button = QPushButton("💾 Save to DB")
    window.save_button.setStyleSheet(_BUTTON_STYLE)
    window.save_button.clicked.connect(lambda: None)  # placeholder

    header_layout.addWidget(title)
    header_layout.addStretch()
    header_layout.addWidget(window.load_data_card)
    header_layout.addWidget(window.analyze_button)
    header_layout.addWidget(window.save_button)

    # Table
    window.excel_table_view = QTableWidget()
    window.excel_table_view.setSortingEnabled(True)
    window.excel_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    window.excel_table_view.horizontalHeader().setStretchLastSection(True)
    window.excel_table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    window.excel_table_view.setAlternatingRowColors(True)
    window.excel_table_view.verticalHeader().setDefaultSectionSize(30)
    window.excel_table_view.verticalHeader().setVisible(False)
    window.excel_table_view.setStyleSheet("""
        QTableWidget { background-color:#fff; border:1px solid #d0d0d0; border-radius:12px;
                       font-size:12pt; gridline-color:#e0e0e0;
                       selection-background-color:#cce6ff; alternate-background-color:#f9f9f9; }
        QHeaderView::section { background-color:#f2f9ff; color:#005999; padding:10px;
                               border:1px solid #d0d0d0; font-weight:bold; font-size:13pt; }
        QTableWidget::item { padding:6px; }
        QTableWidget::item:hover { background-color:#eaf6ff; }
    """)

    outer_layout.addLayout(header_layout)
    outer_layout.addWidget(window.excel_table_view)
    return page


def handle_custom_file_upload(window):
    file_path, _ = QFileDialog.getOpenFileName(
        window, "Select Excel or CSV File", "",
        "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
    )
    if not file_path:
        return
    try:
        df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
        result = _validate_schema(df, file_path)

        msg = QMessageBox(window)
        msg.setWindowTitle("File Validation")
        msg.setText(result["message"])
        if result["status"] == "success":
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            if msg.exec() == QMessageBox.StandardButton.Ok:
                show_table_creation_form(window, df.columns.tolist(), df)
        elif result["status"] == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if msg.exec() == QMessageBox.StandardButton.Ok:
                show_table_creation_form(window, df.columns.tolist(), df)
        else:
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    except Exception as e:
        QMessageBox.critical(window, "File Loading Error", f"❌ Error loading file:\n\n{str(e)}")


def handle_analysis(window):
    dialog = QDialog(window)
    dialog.setWindowTitle("📊 Analyze & Map Data")
    dialog.setMinimumSize(600, 400)

    main_layout = QVBoxLayout(dialog)
    main_layout.setSpacing(15)
    main_layout.setContentsMargins(20, 20, 20, 20)

    header_label = QLabel("Map Spreadsheet Columns to Database")
    header_label.setStyleSheet("font-size:16px; font-weight:bold;")
    main_layout.addWidget(header_label)

    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setFrameShadow(QFrame.Shadow.Sunken)
    main_layout.addWidget(divider)

    mapping_group = QGroupBox("Column Mapping")
    mapping_layout = QVBoxLayout(mapping_group)
    mapping_layout.setSpacing(12)
    mapping_layout.setContentsMargins(15, 20, 15, 15)

    table_label = QLabel("Mapping Table:")
    table_label.setFixedWidth(180)
    table_dropdown = QComboBox()
    table_dropdown.addItems(window.all_tables_name)

    db_col_label = QLabel("Database Column:")
    db_col_label.setFixedWidth(180)
    db_col_dropdown = QComboBox()

    sheet_col_label = QLabel("Spreadsheet Column:")
    sheet_col_label.setFixedWidth(180)
    sheet_col_dropdown = QComboBox()
    if hasattr(window, 'spreadsheet_df') and window.spreadsheet_df is not None:
        sheet_col_dropdown.addItems(window.spreadsheet_df.columns.tolist())

    for lbl, cmb in [(table_label, table_dropdown), (db_col_label, db_col_dropdown),
                     (sheet_col_label, sheet_col_dropdown)]:
        row = QHBoxLayout()
        row.addWidget(lbl)
        row.addWidget(cmb)
        mapping_layout.addLayout(row)

    main_layout.addWidget(mapping_group)

    preview_group = QGroupBox("Preview")
    preview_layout = QVBoxLayout(preview_group)
    preview_text = QTextEdit()
    preview_text.setReadOnly(True)
    preview_text.setMaximumHeight(100)
    preview_layout.addWidget(preview_text)
    main_layout.addWidget(preview_group)

    def update_preview():
        preview_text.setText(
            f"Table: {table_dropdown.currentText()}\n"
            f"DB Column: {db_col_dropdown.currentText()}\n"
            f"Sheet Column: {sheet_col_dropdown.currentText()}"
        )

    def update_db_columns(selected_table):
        try:
            cur = window.db_connection.cursor()
            cur.execute(f"PRAGMA table_info({selected_table});")
            cols = [r[1] for r in cur.fetchall()]
            cur.close()
        except Exception:
            cols = []
        db_col_dropdown.clear()
        db_col_dropdown.addItems(cols)
        update_preview()

    table_dropdown.currentTextChanged.connect(update_db_columns)
    db_col_dropdown.currentTextChanged.connect(update_preview)
    sheet_col_dropdown.currentTextChanged.connect(update_preview)
    if window.all_tables_name:
        update_db_columns(window.all_tables_name[0])

    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    analyze_btn = QPushButton("Analyze Data")

    def run_analysis():
        t = table_dropdown.currentText()
        dc = db_col_dropdown.currentText()
        sc = sheet_col_dropdown.currentText()
        analyze_btn.setText("Processing...")
        analyze_btn.setEnabled(False)
        QApplication.processEvents()
        try:
            dialog.accept()
            matches, unmatched, enriched_df = save_mapping(window.db_connection, window.spreadsheet_df, t, dc, sc)
            _run_analyze_df(window, enriched_df)
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed:\n{str(e)}")
            analyze_btn.setText("Analyze Data")
            analyze_btn.setEnabled(True)

    analyze_btn.clicked.connect(run_analysis)
    btn_layout.addWidget(cancel_btn)
    btn_layout.addWidget(analyze_btn)
    main_layout.addLayout(btn_layout)
    dialog.exec()


def _run_analyze_df(window, df):
    """The analyze_df logic — builds output_list and calls show_dashboard."""
    import calendar
    col_521 = next((col for col in df.columns if "521" in col), None)
    if not col_521:
        QMessageBox.warning(window, "Warning", "No 521 ID column found in data.")
        return

    from core.db import get_holidays_for_year
    from core.utils import date_calculation
    import json

    cur = window.db_connection.cursor()
    cur.execute("SELECT year, holidays FROM holiday")
    holiday_map = {}
    for year, hj in cur.fetchall():
        try:
            holiday_map[year] = json.loads(hj)
        except Exception:
            holiday_map[year] = []
    cur.close()

    from datetime import datetime
    grouped = df.groupby(col_521)
    output_list = []

    for group_name, group_df in grouped:
        group_df = group_df.copy()
        group_df['Start Date'] = pd.to_datetime(group_df['Start Date'])
        group_df['End Date'] = pd.to_datetime(group_df['End Date'])
        group_df = group_df.sort_values('Start Date')
        full_name = group_df['Opened By'].iloc[0]
        month_year_leave_dates = {}

        for _, row in group_df.iterrows():
            all_dates = pd.date_range(row['Start Date'], row['End Date'])
            workdays = all_dates[~all_dates.weekday.isin([5, 6])]
            for d in workdays:
                key = (d.year, d.month)
                month_year_leave_dates.setdefault(key, set()).add(d)

        for (year, month), dates in sorted(month_year_leave_dates.items()):
            dates_sorted = sorted(dates)
            dates_str = [d.strftime("%A, %B %d, %Y") for d in dates_sorted]
            month_name = dates_sorted[0].strftime("%B")
            num_days = calendar.monthrange(year, month)[1]
            all_days = pd.date_range(f"{year}-{month:02d}-01", f"{year}-{month:02d}-{num_days}")
            total_working = len(all_days[~all_days.weekday.isin([5, 6])])
            holidays_month = []
            holiday_weekdays = []
            for h in holiday_map.get(str(year), []):
                try:
                    dt = datetime.strptime(h, "%d-%m-%Y")
                    if dt.year == year and dt.month == month:
                        holidays_month.append(dt.strftime("%A, %B %d, %Y"))
                        if dt.weekday() not in [5, 6]:
                            holiday_weekdays.append(dt)
                except Exception:
                    continue

            output_list.append({
                "Group Name": group_name, "Full Name": full_name,
                "Month": month_name, "Year": year,
                "Leave Taken Days": len(dates_sorted), "Dates of Leave": dates_str,
                "Total Billable Days": total_working - len(holiday_weekdays),
                "Total Working Days": total_working,
                "Holidays": holidays_month or None,
            })

    show_dashboard(output_list)


def show_table_creation_form(window, headers: list, df):
    dialog = QDialog(window)
    dialog.setWindowTitle("Define Table Structure")
    dialog.resize(700, 500)
    main_layout = QVBoxLayout(dialog)

    table_name_input = QLineEdit()
    table_name_input.setPlaceholderText("Enter Table Name")
    main_layout.addWidget(QLabel("Table Name:"))
    main_layout.addWidget(table_name_input)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    grid = QGridLayout(scroll_widget)
    grid.setSpacing(15)

    dropdowns = {}
    for row_idx, header in enumerate(headers):
        lbl = QLabel(str(header))
        combo = QComboBox()
        combo.addItems(["TEXT", "INTEGER", "REAL", "DATE"])
        dropdowns[header] = combo
        col = row_idx // ((len(headers) + 1) // 2)
        grid.addWidget(lbl, row_idx % ((len(headers) + 1) // 2), col * 2)
        grid.addWidget(combo, row_idx % ((len(headers) + 1) // 2), col * 2 + 1)

    scroll.setWidget(scroll_widget)
    main_layout.addWidget(scroll)

    submit_btn = QPushButton("Load Table")
    submit_btn.setEnabled(False)
    main_layout.addWidget(submit_btn)

    regex = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    reserved = {'SELECT','CREATE','TABLE','FROM','WHERE','AND','OR','NOT','INSERT','INTO',
                'UPDATE','SET','DELETE','GROUP','BY','ORDER','JOIN','PRIMARY','KEY','NULL','UNIQUE'}

    def is_valid(name):
        return bool(name) and bool(regex.match(name)) and name.upper() not in reserved

    def check():
        ok = is_valid(table_name_input.text().strip())
        table_name_input.setStyleSheet("" if ok else "background-color:#ffe6e6;")
        submit_btn.setEnabled(ok)

    table_name_input.textChanged.connect(check)
    for cb in dropdowns.values():
        cb.currentIndexChanged.connect(check)

    def on_submit():
        table_name = table_name_input.text().strip()
        col_defs = {col: dropdowns[col].currentText() for col in headers}
        _create_and_show_table(window, table_name, col_defs, df)
        dialog.accept()

    submit_btn.clicked.connect(on_submit)
    check()
    dialog.exec()


def _create_and_show_table(window, table_name, column_defs, df):
    if df.empty:
        window.excel_table_view.clear()
        return

    columns = df.columns.tolist()
    num_rows, num_cols = df.shape

    base_style = _BUTTON_STYLE
    if set(columns) == _REQUIRED_COLS:
        window.analyze_button.setEnabled(True)
        window.analyze_button.setStyleSheet(base_style + "QPushButton { background-color:#3498db; color:white; }")
    else:
        window.analyze_button.setEnabled(False)
        window.analyze_button.setStyleSheet(base_style + "QPushButton { background-color:#bdc3c7; color:#7f8c8d; }")

    window.spreadsheet_table_name = table_name
    window.spreadsheet_df = df
    window.column_defs = column_defs

    window.excel_table_view.setUpdatesEnabled(False)
    window.excel_table_view.setSortingEnabled(False)
    try:
        window.excel_table_view.clearContents()
        window.excel_table_view.setRowCount(num_rows)
        window.excel_table_view.setColumnCount(num_cols)
        window.excel_table_view.setHorizontalHeaderLabels(columns)
        _configure_table(window)
        _populate_table(window, df, num_rows, num_cols)
    finally:
        window.excel_table_view.setUpdatesEnabled(True)
        window.excel_table_view.setSortingEnabled(True)


def _configure_table(window):
    table = window.excel_table_view
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    table.verticalHeader().setDefaultSectionSize(25)
    default_width = 250 if table.columnCount() <= 3 else 150
    for col in range(table.columnCount()):
        table.setColumnWidth(col, default_width)


def _populate_table(window, df, num_rows, num_cols):
    import pandas as pd
    non_editable = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
    align_right = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
    align_left = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
    colors = {
        'positive': QColor("#2e7d32"), 'negative': QColor("#c62828"),
        'zero': QColor("#1565c0"), 'default': QColor("#2c3e50"),
    }
    chunk_size = min(1000, num_rows)
    for chunk_start in range(0, num_rows, chunk_size):
        chunk_end = min(chunk_start + chunk_size, num_rows)
        for local_idx, (_, row) in enumerate(df.iloc[chunk_start:chunk_end].iterrows()):
            actual_row = chunk_start + local_idx
            for col_idx, value in enumerate(row):
                if pd.isna(value) or value is None:
                    text, color_key, align = "", "default", align_left
                elif isinstance(value, bool):
                    text, color_key, align = ("Yes" if value else "No"), "default", align_left
                elif isinstance(value, float):
                    text = f"{value:.4f}"
                    color_key = "positive" if value > 0 else ("negative" if value < 0 else "zero")
                    align = align_right
                elif isinstance(value, int):
                    text = str(value)
                    color_key = "positive" if value > 0 else "zero"
                    align = align_right
                else:
                    text, color_key, align = str(value), "default", align_left

                item = QTableWidgetItem(text)
                item.setTextAlignment(align)
                item.setFlags(non_editable)
                if color_key in colors:
                    item.setForeground(colors[color_key])
                window.excel_table_view.setItem(actual_row, col_idx, item)


def _validate_schema(df, file_path) -> dict:
    if df.empty:
        return {"status": "error", "message": "❌ File is empty."}
    errors, warnings = [], []
    cols = df.columns.tolist()

    for i, col in enumerate(cols):
        col_str = str(col).strip()
        if not col_str or col_str.lower() in ('nan', 'unnamed'):
            errors.append(f"Column {i+1}: empty/invalid header")
        if cols.count(col) > 1:
            errors.append(f"Column '{col_str}': duplicate header")

    if df.isna().all().all():
        errors.append("All rows are empty")

    empty_rows = df.index[df.isna().all(axis=1)].tolist()
    if len(empty_rows) > len(df) * 0.5:
        errors.append(f"Too many empty rows ({len(empty_rows)}/{len(df)})")

    for col in df.columns:
        non_null = df[col].dropna()
        if len(non_null) > 0 and len(set(type(v).__name__ for v in non_null)) > 2:
            warnings.append(f"Column '{col}': mixed data types")

    if errors:
        return {"status": "error", "message": "❌ Validation Failed:\n• " + "\n• ".join(errors)}
    if warnings:
        return {"status": "warning", "message": "⚠️ Warnings:\n• " + "\n• ".join(warnings) + "\n\nProceed anyway?"}
    return {"status": "success", "message": (
        f"✅ Validation successful!\n\n📄 {file_path.split('/')[-1]}\n"
        f"📊 Rows: {len(df)}\n📋 Columns: {len(df.columns)}"
    )}
