# ======================
# ui/pages/database_page.py — Database viewer with table browser, edit, delete
# ======================
import re
import sqlite3

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDialog,
    QScrollArea, QTextEdit, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QIcon, QFont
from PyQt6.QtCore import Qt


def create_database_page(window) -> QWidget:
    """Build and return the Database page widget."""
    page = QWidget()
    main_layout = QVBoxLayout(page)
    main_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.setSpacing(15)

    # Header
    header = QLabel("📁 Database Manager")
    header.setStyleSheet("font-size:18px; font-weight:bold;")
    main_layout.addWidget(header)

    # Controls row
    ctrl_layout = QHBoxLayout()
    ctrl_layout.setSpacing(10)

    window.db_table_combo = QComboBox()
    window.db_table_combo.setMinimumWidth(200)
    window.db_table_combo.setFixedHeight(35)
    window.db_table_combo.currentTextChanged.connect(lambda t: show_table_contents(window, t))

    window.delete_table_btn = QPushButton("🗑 Delete Table")
    window.delete_table_btn.setFixedHeight(35)
    window.delete_table_btn.setStyleSheet(
        "QPushButton{background:#D32F2F;color:white;border-radius:4px;padding:6px 12px;}"
        "QPushButton:hover{background:#E53935;}"
    )
    window.delete_table_btn.clicked.connect(lambda: delete_current_table(window))

    window.export_btn = QPushButton("📤 Export")
    window.export_btn.setFixedHeight(35)
    window.export_btn.setStyleSheet(
        "QPushButton{background:#1976d2;color:white;border-radius:4px;padding:6px 12px;}"
        "QPushButton:hover{background:#1565c0;}"
    )

    ctrl_layout.addWidget(QLabel("Table:"))
    ctrl_layout.addWidget(window.db_table_combo)
    ctrl_layout.addWidget(window.delete_table_btn)
    ctrl_layout.addWidget(window.export_btn)
    ctrl_layout.addStretch()
    main_layout.addLayout(ctrl_layout)

    # Filter row placeholder (populated when table is selected)
    window.filter_row_widget = QWidget()
    window.filter_row_layout = QHBoxLayout(window.filter_row_widget)
    window.filter_row_layout.setSpacing(5)
    window.filter_inputs = []
    main_layout.addWidget(window.filter_row_widget)

    # Table view
    window.table_view = QTableWidget()
    window.table_view.setAlternatingRowColors(True)
    window.table_view.setSortingEnabled(True)
    window.table_view.horizontalHeader().setStretchLastSection(False)
    window.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    window.table_view.verticalHeader().setVisible(False)
    window.table_view.setStyleSheet("""
        QTableWidget { background:#fff; border:1px solid #ddd; font-size:11px; }
        QHeaderView::section { background:#f8f9fa; color:#495057; font-weight:bold; padding:8px; border:1px solid #dee2e6; }
        QTableWidget::item { padding:6px; }
        QTableWidget::item:selected { background:#e3f2fd; }
    """)
    main_layout.addWidget(window.table_view)

    # Status bar
    window.db_status_label = QLabel("Select a table to view its contents")
    window.db_status_label.setStyleSheet("color:#666; font-size:11px;")
    main_layout.addWidget(window.db_status_label)

    return page


def show_table_contents(window, table_name: str):
    if not table_name:
        return
    window.current_table = table_name
    cursor = None
    try:
        cursor = window.db_connection.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}"')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Rebuild filter row
        for i in reversed(range(window.filter_row_layout.count())):
            item = window.filter_row_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        window.filter_inputs = []

        for col in columns:
            fe = QLineEdit()
            fe.setPlaceholderText(f"Filter {col}")
            fe.setFixedHeight(28)
            fe.textChanged.connect(lambda: apply_filters(window))
            window.filter_row_layout.addWidget(fe)
            window.filter_inputs.append(fe)

        # Populate table
        window.table_view.setUpdatesEnabled(False)
        window.table_view.clearContents()
        window.table_view.setRowCount(len(rows))
        window.table_view.setColumnCount(len(columns) + 1)
        window.table_view.setHorizontalHeaderLabels(columns + ["Actions"])

        action_column_width = 120
        window.table_view.horizontalHeader().setSectionResizeMode(
            len(columns), QHeaderView.ResizeMode.Fixed
        )
        window.table_view.setColumnWidth(len(columns), action_column_width)

        for row_idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value) if value is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if isinstance(value, (int, float)) and value != 0:
                    item.setForeground(QColor("#1976d2"))
                window.table_view.setItem(row_idx, col_idx, item)

            # Action buttons
            from PyQt6.QtWidgets import QWidget as _QW, QHBoxLayout as _HL
            action_widget = _QW()
            action_widget.setStyleSheet("background:transparent;")
            action_layout = _HL(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(50, 28)
            edit_btn.setToolTip("Edit Record")
            edit_btn.setStyleSheet(
                "QPushButton{background:#FFB300;color:white;border:none;border-radius:14px;font-size:12px;}"
                "QPushButton:hover{background:#FFA000;}"
            )
            edit_btn.clicked.connect(lambda _, r=row, tn=table_name: open_edit_dialog(window, tn, r))

            del_btn = QPushButton("Delete")
            del_btn.setFixedSize(60, 28)
            del_btn.setToolTip("Delete Record")
            del_btn.setStyleSheet(
                "QPushButton{background:#D32F2F;color:white;border:none;border-radius:14px;font-size:12px;}"
                "QPushButton:hover{background:#E53935;}"
            )
            del_btn.clicked.connect(lambda _, r=row, tn=table_name: delete_row(window, tn, r))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            window.table_view.setCellWidget(row_idx, len(columns), action_widget)

        window.table_view.setUpdatesEnabled(True)
        window.table_view.resizeColumnsToContents()
        apply_filters(window)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        window.table_view.setGraphicsEffect(shadow)

        window.db_status_label.setText(f"Table: {table_name} — {len(rows)} row(s)")

    except sqlite3.Error as e:
        QMessageBox.critical(window, "Database Error", f"Failed to load table:\n{str(e)}")
    finally:
        if cursor:
            cursor.close()


def apply_filters(window):
    try:
        filters = [fe.text().strip().lower() for fe in window.filter_inputs]
        for row in range(window.table_view.rowCount()):
            show = True
            for col, f in enumerate(filters):
                if f:
                    item = window.table_view.item(row, col)
                    if not item or f not in item.text().lower():
                        show = False
                        break
            window.table_view.setRowHidden(row, not show)
    except Exception as e:
        print(f"Filter error: {e}")


def open_edit_dialog(window, table_name: str, row_data):
    dialog = QDialog(window)
    dialog.setWindowTitle(f"Edit Record — {table_name}")
    dialog.setMinimumSize(800, 600)

    main_layout = QVBoxLayout(dialog)
    main_layout.setContentsMargins(30, 30, 30, 30)
    main_layout.setSpacing(25)

    hdr = QLabel(f"Editing Record in '{table_name}'")
    hdr.setStyleSheet("font-size:20px;font-weight:bold;color:#2c3e50;padding-bottom:15px;border-bottom:2px solid #3498db;")
    main_layout.addWidget(hdr)

    cursor = window.db_connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    cursor.close()

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    content = QWidget()
    form_layout = QVBoxLayout(content)
    form_layout.setSpacing(30)

    input_fields = {}
    for col_name, value in zip(columns, row_data):
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setSpacing(8)
        lbl = QLabel(col_name)
        lbl.setStyleSheet("font-size:14px;font-weight:bold;color:#34495e;")
        use_textedit = isinstance(value, str) and len(str(value)) > 50
        field = QTextEdit() if use_textedit else QLineEdit()
        if isinstance(field, QLineEdit):
            field.setText(str(value))
            field.setClearButtonEnabled(True)
        else:
            field.setPlainText(str(value))
        field.setStyleSheet(
            "QLineEdit,QTextEdit{font-size:16px;padding:12px;border:2px solid #bdc3c7;"
            "border-radius:6px;min-height:50px;}"
            "QLineEdit:focus,QTextEdit:focus{border-color:#3498db;}"
        )
        cl.addWidget(lbl)
        cl.addWidget(field)
        form_layout.addWidget(container)
        input_fields[col_name] = field

    scroll.setWidget(content)
    main_layout.addWidget(scroll)

    btn_container = QWidget()
    btn_layout = QHBoxLayout(btn_container)
    save_btn = QPushButton(" Save Changes")
    save_btn.setStyleSheet(
        "QPushButton{background:#27ae60;color:white;border:none;padding:15px 30px;"
        "border-radius:6px;font-size:16px;min-width:150px;}"
        "QPushButton:hover{background:#219a52;}"
    )
    save_btn.clicked.connect(lambda: _save_edited_row(window, dialog, table_name, columns, row_data, input_fields))

    cancel_btn = QPushButton("Cancel")
    cancel_btn.setStyleSheet(
        "QPushButton{background:#e74c3c;color:white;border:none;padding:15px 30px;"
        "border-radius:6px;font-size:16px;min-width:150px;}"
        "QPushButton:hover{background:#c0392b;}"
    )
    cancel_btn.clicked.connect(dialog.reject)

    btn_layout.addStretch()
    btn_layout.addWidget(cancel_btn)
    btn_layout.addWidget(save_btn)
    main_layout.addWidget(btn_container)
    dialog.exec()


def _save_edited_row(window, dialog, table_name, columns, old_row_data, input_fields):
    cursor = None
    try:
        cursor = window.db_connection.cursor()

        def get_val(w):
            if hasattr(w, 'text'):        return w.text()
            if hasattr(w, 'toPlainText'): return w.toPlainText()
            return str(w)

        def normalize(v):
            return None if (v is None or v == "") else str(v).strip()

        new_values = [normalize(get_val(input_fields[c])) for c in columns]
        old_values = [normalize(v) for v in old_row_data]

        if new_values == old_values:
            QMessageBox.information(window, "No Changes", "No changes made.")
            dialog.close()
            return

        conditions, params = [], []
        for col, val in zip(columns, old_row_data):
            if val is None:
                conditions.append(f'"{col}" IS NULL')
            else:
                conditions.append(f'"{col}" = ?')
                params.append(val)

        where = " AND ".join(conditions)
        cursor.execute(f'SELECT ROWID FROM "{table_name}" WHERE {where} LIMIT 1', params)
        rowid_res = cursor.fetchone()
        if not rowid_res:
            QMessageBox.warning(window, "Error", "Record not found.")
            return

        set_clause = ", ".join([f'"{c}" = ?' for c in columns])
        cursor.execute(f'UPDATE "{table_name}" SET {set_clause} WHERE ROWID = ?',
                       new_values + [rowid_res[0]])
        if cursor.rowcount > 0:
            window.db_connection.commit()
            QMessageBox.information(window, "Success", "Record updated successfully!")
            dialog.close()
            show_table_contents(window, table_name)
        else:
            QMessageBox.warning(window, "Warning", "No record was updated.")

    except sqlite3.Error as e:
        window.db_connection.rollback()
        QMessageBox.critical(window, "Database Error", str(e))
    finally:
        if cursor:
            cursor.close()


def delete_row(window, table_name: str, row_data):
    confirm = QMessageBox.question(window, "Confirm Delete",
                                   "Are you sure you want to delete this record?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if confirm != QMessageBox.StandardButton.Yes:
        return
    try:
        cursor = window.db_connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        col_names = [c[1] for c in cursor.fetchall()]

        conditions, values = [], []
        for col, val in zip(col_names, row_data):
            if val not in (None, ''):
                conditions.append(f"{col} = ?")
                values.append(val)
            else:
                conditions.append(f"{col} IS NULL")

        cursor.execute(f"DELETE FROM {table_name} WHERE {' AND '.join(conditions)}", values)
        window.db_connection.commit()

        if cursor.rowcount > 0:
            QMessageBox.information(window, "Deleted", "Record deleted successfully.")
            show_table_contents(window, table_name)
        else:
            QMessageBox.warning(window, "Warning", "No matching record found.")
        cursor.close()
    except sqlite3.Error as e:
        QMessageBox.critical(window, "Error", f"Failed to delete record:\n{str(e)}")


def delete_current_table(window):
    if not window.current_table:
        QMessageBox.warning(window, "No Table Selected", "Please select a table first.")
        return
    confirm = QMessageBox.question(
        window, "Confirm Delete",
        f"Permanently delete table '{window.current_table}'?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if confirm != QMessageBox.StandardButton.Yes:
        return
    try:
        cursor = window.db_connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS '{window.current_table}'")
        window.db_connection.commit()
        cursor.close()
        QMessageBox.information(window, "Deleted", f"Table '{window.current_table}' deleted.")
        window.initialize_database()
        window.table_view.clear()
        window.current_table = None
        if window.all_tables_name:
            show_table_contents(window, window.all_tables_name[0])
    except sqlite3.Error as e:
        QMessageBox.critical(window, "Database Error", f"Failed to delete table:\n{str(e)}")
