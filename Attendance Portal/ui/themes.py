# ======================
# ui/themes.py — Premium Dark & Light Themes
# ======================

# ── Color tokens ────────────────────────────────────────────────────────────
# Accent:   #00c9a7  (emerald-teal)
# Accent2:  #845ec2  (soft violet — used for secondary)
# Dark bg:  #0f1117
# Dark card:#1a1d27
# Dark sidebar: #13151f
# ─────────────────────────────────────────────────────────────────────────────

DARK_THEME = """
/* ── Base ──────────────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #0f1117;
}
QWidget {
    background-color: #0f1117;
    color: #e2e8f0;
    font-family: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ────────────────────────────────────────────────────── */
QFrame#sidebar {
    background-color: #13151f;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ── Nav buttons ────────────────────────────────────────────────── */
QPushButton#nav_btn {
    text-align: left;
    padding-left: 14px;
    border-radius: 10px;
    border: none;
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
    background-color: transparent;
}
QPushButton#nav_btn:hover {
    background-color: rgba(0, 201, 167, 0.10);
    color: #e2e8f0;
}
QPushButton#nav_btn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: #ffffff;
    font-weight: 600;
}

/* ── Theme toggle button ─────────────────────────────────────────── */
QPushButton#theme_btn {
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 8px;
    color: #94a3b8;
    padding: 6px;
    font-size: 12px;
}
QPushButton#theme_btn:hover {
    background-color: rgba(0,201,167,0.12);
    border-color: #00c9a7;
    color: #00c9a7;
}

/* ── Stacked / content area ─────────────────────────────────────── */
QStackedWidget > QWidget {
    background-color: #0f1117;
}

/* ── Group boxes ─────────────────────────────────────────────────── */
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    color: #64748b;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    margin-top: 10px;
    padding-top: 14px;
    background-color: #1a1d27;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    top: -1px;
    color: #00c9a7;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Inputs ──────────────────────────────────────────────────────── */
QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: #1e2130;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 12px;
    color: #e2e8f0;
    selection-background-color: #00c9a7;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #00c9a7;
    background-color: #1e2130;
}

/* ── ComboBox ────────────────────────────────────────────────────── */
QComboBox {
    background-color: #1e2130;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 7px 12px;
    color: #e2e8f0;
    min-height: 32px;
}
QComboBox:focus { border-color: #00c9a7; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border: none;
}
QComboBox::down-arrow {
    image: none;
    width: 10px; height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #1e2130;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 8px;
    color: #e2e8f0;
    selection-background-color: #00c9a7;
    selection-color: #0f1117;
    outline: none;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1e2130;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 16px;
    color: #e2e8f0;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #252a3d;
    border-color: rgba(0,201,167,0.40);
}
QPushButton:pressed {
    background-color: rgba(0,201,167,0.15);
}
QPushButton:disabled {
    background-color: #1a1d27;
    color: #3d4663;
    border-color: transparent;
}

/* ── Accent generate button ─────────────────────────────────────── */
QPushButton#generate_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: #0f1117;
    font-weight: 700;
    font-size: 14px;
    border: none;
    border-radius: 10px;
    letter-spacing: 0.3px;
}
QPushButton#generate_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00dbb8, stop:1 #00c9a7);
}
QPushButton#generate_button:disabled {
    background-color: #2a2f42;
    color: #3d4663;
}

/* Holiday / Format buttons */
QPushButton#load_holiday_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: #0f1117; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#load_holiday_btn:hover { background-color: #00dbb8; }

QPushButton#view_holiday_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #845ec2, stop:1 #6b45a8);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#view_holiday_btn:hover { background-color: #9d6fd4; }

QPushButton#format_info_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0096c7, stop:1 #007baa);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#format_info_btn:hover { background-color: #00b4e0; }

QPushButton#upload_button, QPushButton#category_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #f77f00, stop:1 #d96200);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#upload_button:hover, QPushButton#category_btn:hover {
    background-color: #ff9500;
}

/* ── Progress bar ────────────────────────────────────────────────── */
QProgressBar {
    height: 10px;
    border: none;
    border-radius: 5px;
    background-color: #1e2130;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    border-radius: 5px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c9a7, stop:1 #845ec2);
}

/* ── Table ───────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #1a1d27;
    color: #e2e8f0;
    border: none;
    border-radius: 10px;
    gridline-color: rgba(255,255,255,0.04);
    alternate-background-color: #1e2130;
}
QHeaderView::section {
    background-color: #13151f;
    color: #00c9a7;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    border: none;
    border-bottom: 2px solid rgba(0,201,167,0.2);
}
QTableWidget::item {
    padding: 8px;
    color: #cbd5e1;
    border: none;
}
QTableWidget::item:selected {
    background-color: rgba(0,201,167,0.15);
    color: #e2e8f0;
}
QTableWidget::item:hover {
    background-color: rgba(0,201,167,0.08);
}

/* ── ScrollBar ───────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(148,163,184,0.25);
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: rgba(0,201,167,0.5); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent; height: 6px; margin: 0;
}
QScrollBar::handle:horizontal {
    background: rgba(148,163,184,0.25);
    border-radius: 3px; min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: rgba(0,201,167,0.5); }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Tooltips ────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1e2130;
    color: #e2e8f0;
    border: 1px solid rgba(0,201,167,0.3);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Status message ──────────────────────────────────────────────── */
QLabel#statusMsg[messageType="error"] {
    color: #fb7185;
    background-color: rgba(251,113,133,0.10);
    border: 1px solid rgba(251,113,133,0.30);
    border-radius: 8px;
    padding: 10px 14px;
}
QLabel#statusMsg[messageType="success"] {
    color: #34d399;
    background-color: rgba(52,211,153,0.10);
    border: 1px solid rgba(52,211,153,0.30);
    border-radius: 8px;
    padding: 10px 14px;
}
QLabel#statusMsg[messageType="info"] {
    color: #60a5fa;
    background-color: rgba(96,165,250,0.10);
    border: 1px solid rgba(96,165,250,0.30);
    border-radius: 8px;
    padding: 10px 14px;
}

/* ── Message box ─────────────────────────────────────────────────── */
QMessageBox {
    background-color: #1a1d27;
}
QMessageBox QLabel { color: #e2e8f0; }
QMessageBox QPushButton {
    min-width: 80px; min-height: 32px;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: #0f1117; font-weight: 600; border: none; border-radius: 6px;
}
"""

# ─────────────────────────────────────────────────────────────────────────────
LIGHT_THEME = """
/* ── Base ──────────────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #f0f4f8;
}
QWidget {
    background-color: #f0f4f8;
    color: #1e293b;
    font-family: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ────────────────────────────────────────────────────── */
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
    border-right: none;
}

/* ── Nav buttons ────────────────────────────────────────────────── */
QPushButton#nav_btn {
    text-align: left;
    padding-left: 14px;
    border-radius: 10px;
    border: none;
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
    background-color: transparent;
}
QPushButton#nav_btn:hover {
    background-color: rgba(255,255,255,0.08);
    color: #f1f5f9;
}
QPushButton#nav_btn:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: #0f172a;
    font-weight: 700;
}

/* ── Theme toggle ───────────────────────────────────────────────── */
QPushButton#theme_btn {
    background-color: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 8px;
    color: #94a3b8;
    padding: 6px;
    font-size: 12px;
}
QPushButton#theme_btn:hover {
    background-color: rgba(0,201,167,0.15);
    border-color: #00c9a7;
    color: #00c9a7;
}

/* ── Content ────────────────────────────────────────────────────── */
QStackedWidget > QWidget { background-color: #f0f4f8; }

/* ── Group boxes ─────────────────────────────────────────────────── */
QGroupBox {
    font-weight: 600;
    font-size: 11px;
    color: #64748b;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    margin-top: 10px;
    padding-top: 14px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    top: -1px;
    color: #00a88e;
    font-size: 11px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Inputs ──────────────────────────────────────────────────────── */
QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    color: #1e293b;
    selection-background-color: #00c9a7;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #00c9a7;
}

/* ── ComboBox ────────────────────────────────────────────────────── */
QComboBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 7px 12px;
    color: #1e293b;
    min-height: 32px;
}
QComboBox:focus { border-color: #00c9a7; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    color: #1e293b;
    selection-background-color: #00c9a7;
    selection-color: #ffffff;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 16px;
    color: #374151;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #f8fafc;
    border-color: #00c9a7;
    color: #00a88e;
}
QPushButton:pressed { background-color: #f0fdfb; }
QPushButton:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* ── Accent generate button ─────────────────────────────────────── */
QPushButton#generate_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: #ffffff;
    font-weight: 700;
    font-size: 14px;
    border: none;
    border-radius: 10px;
}
QPushButton#generate_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00dbb8, stop:1 #00c9a7);
}

/* Holiday / Format / Upload */
QPushButton#load_holiday_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #00c9a7, stop:1 #00a88e);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#view_holiday_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #845ec2, stop:1 #6b45a8);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#format_info_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0096c7, stop:1 #007baa);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}
QPushButton#upload_button, QPushButton#category_btn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #f77f00, stop:1 #d96200);
    color: white; border: none; border-radius: 8px; font-weight: 600;
}

/* ── Progress bar ────────────────────────────────────────────────── */
QProgressBar {
    height: 10px;
    border: none;
    border-radius: 5px;
    background-color: #e2e8f0;
    color: transparent;
}
QProgressBar::chunk {
    border-radius: 5px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c9a7, stop:1 #845ec2);
}

/* ── Table ───────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: #f1f5f9;
    alternate-background-color: #f8fafc;
}
QHeaderView::section {
    background-color: #f8fafc;
    color: #00a88e;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
    border: none;
    border-bottom: 2px solid #e2e8f0;
}
QTableWidget::item { padding: 8px; color: #374151; }
QTableWidget::item:selected {
    background-color: rgba(0,201,167,0.12);
    color: #1e293b;
}
QTableWidget::item:hover { background-color: #f0fdfb; }

/* ── ScrollBar ───────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent; width: 6px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1; border-radius: 3px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #00c9a7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: transparent; height: 6px; margin: 0;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1; border-radius: 3px; min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #00c9a7; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Tooltips ────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1e293b;
    color: #e2e8f0;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Status message ──────────────────────────────────────────────── */
QLabel#statusMsg[messageType="error"] {
    color: #dc2626;
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 10px 14px;
}
QLabel#statusMsg[messageType="success"] {
    color: #059669;
    background-color: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 8px;
    padding: 10px 14px;
}
QLabel#statusMsg[messageType="info"] {
    color: #2563eb;
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 10px 14px;
}
"""
