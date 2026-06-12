# ======================
# ui/pages/settings_page.py
# ======================
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QMessageBox, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt

from core.db import get_settings, save_settings

def create_settings_page(window) -> QWidget:
    page = QWidget()
    outer = QVBoxLayout(page)
    outer.setContentsMargins(40, 40, 40, 40)
    outer.setSpacing(20)
    outer.setAlignment(Qt.AlignmentFlag.AlignTop)

    # Header
    header = QLabel("⚙️  App Settings")
    header.setStyleSheet("font-size: 24px; font-weight: 700; margin-bottom: 6px;")
    outer.addWidget(header)

    sub = QLabel("Configure global default preferences for the Attendance Portal.")
    sub.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 20px;")
    outer.addWidget(sub)

    # Card Container
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 20px;
        }
    """)
    if window.styleSheet() and "background: #0f1117" in window.styleSheet():
        # Dark mode adaptation fallback (if custom theme is dark)
        card.setStyleSheet("""
            QFrame {
                background: #1e1e24;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.1);
                padding: 20px;
            }
        """)

    card_layout = QVBoxLayout(card)
    card_layout.setSpacing(15)

    form_layout = QFormLayout()
    form_layout.setSpacing(20)

    # Settings fields
    threshold_spin = QSpinBox()
    threshold_spin.setRange(50, 100)
    threshold_spin.setValue(90)
    threshold_spin.setSuffix(" %")
    threshold_spin.setFixedHeight(35)
    threshold_spin.setStyleSheet("QSpinBox { padding: 5px; border: 1px solid #cbd5e1; border-radius: 5px; }")

    calc_base_combo = QComboBox()
    calc_base_combo.addItems(["Total Working Days", "Total Billable Days"])
    calc_base_combo.setFixedHeight(35)
    calc_base_combo.setStyleSheet("QComboBox { padding: 5px; border: 1px solid #cbd5e1; border-radius: 5px; }")

    auto_clean_cb = QCheckBox("Enable automated data cleaning for spreadsheets")
    auto_clean_cb.setChecked(True)
    auto_clean_cb.setStyleSheet("QCheckBox { font-size: 13px; }")

    form_layout.addRow(QLabel("Default Attendance Threshold:"), threshold_spin)
    form_layout.addRow(QLabel("Default Calculation Base:"), calc_base_combo)
    form_layout.addRow(QLabel("Data Processing:"), auto_clean_cb)

    card_layout.addLayout(form_layout)
    outer.addWidget(card)

    # Load current settings from DB
    current_settings = get_settings(window.db_connection)
    if "default_threshold" in current_settings:
        try:
            threshold_spin.setValue(int(current_settings["default_threshold"]))
        except ValueError:
            pass
    if "default_calc_base" in current_settings:
        idx = calc_base_combo.findText(current_settings["default_calc_base"])
        if idx >= 0:
            calc_base_combo.setCurrentIndex(idx)
    if "auto_clean" in current_settings:
        auto_clean_cb.setChecked(current_settings["auto_clean"] == "True")

    # Save Button
    btn_layout = QHBoxLayout()
    save_btn = QPushButton("Save Settings")
    save_btn.setFixedHeight(40)
    save_btn.setFixedWidth(150)
    save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    save_btn.setStyleSheet("""
        QPushButton {
            background: #2563eb;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            font-size: 14px;
        }
        QPushButton:hover {
            background: #1d4ed8;
        }
    """)
    
    def on_save():
        settings_to_save = {
            "default_threshold": str(threshold_spin.value()),
            "default_calc_base": calc_base_combo.currentText(),
            "auto_clean": str(auto_clean_cb.isChecked())
        }
        if save_settings(window.db_connection, settings_to_save):
            QMessageBox.information(window, "Success", "Settings saved successfully!")
            # Also apply these settings to window properties if needed
            window.app_settings = settings_to_save
        else:
            QMessageBox.critical(window, "Error", "Failed to save settings to database.")

    save_btn.clicked.connect(on_save)
    btn_layout.addStretch()
    btn_layout.addWidget(save_btn)
    
    outer.addLayout(btn_layout)
    outer.addStretch()

    return page
