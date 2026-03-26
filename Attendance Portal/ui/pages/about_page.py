# ======================
# ui/pages/about_page.py
# ======================
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt
from config import APP_NAME, VERSION, BUILD_DATE


def create_about_page() -> QWidget:
    page = QWidget()
    outer = QVBoxLayout(page)
    outer.setContentsMargins(40, 40, 40, 40)
    outer.setAlignment(Qt.AlignmentFlag.AlignTop)

    # ── Page header ──────────────────────────────────────────────────────
    header = QLabel("ℹ️  About")
    header.setStyleSheet("font-size: 24px; font-weight: 700; margin-bottom: 6px;")
    outer.addWidget(header)

    sub = QLabel("Learn about this application and its dependencies.")
    sub.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 24px;")
    outer.addWidget(sub)

    # ── Card ─────────────────────────────────────────────────────────────
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            border-radius: 14px;
            padding: 30px;
        }
    """)
    card_layout = QVBoxLayout(card)
    card_layout.setSpacing(20)

    # App identity block
    identity = QLabel(
        f"<h2 style='margin:0;font-size:20px;'>⚡ AttendanceBI</h2>"
        f"<p style='color:#64748b;font-size:12px;margin:4px 0 0 0;'>v{VERSION}  •  Build: {BUILD_DATE}</p>"
    )
    identity.setTextFormat(Qt.TextFormat.RichText)
    card_layout.addWidget(identity)

    # Divider
    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setStyleSheet("background: rgba(148,163,184,0.15);")
    divider.setFixedHeight(1)
    card_layout.addWidget(divider)

    # Ownership
    owner_lbl = QLabel(
        "<p style='margin:0;font-size:13px;'>"
        "🏢  <b>Proprietary Software</b> — Hitachi Digital Service<br>"
        "👤  Developed by <b>Vimit</b>"
        "</p>"
    )
    owner_lbl.setTextFormat(Qt.TextFormat.RichText)
    card_layout.addWidget(owner_lbl)

    # Divider
    divider2 = QFrame()
    divider2.setFrameShape(QFrame.Shape.HLine)
    divider2.setStyleSheet("background: rgba(148,163,184,0.15);")
    divider2.setFixedHeight(1)
    card_layout.addWidget(divider2)

    # Tech stack as pills
    stack_title = QLabel("Built With")
    stack_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b; letter-spacing: 0.5px;")
    card_layout.addWidget(stack_title)

    pills_row = QHBoxLayout()
    pills_row.setSpacing(10)
    pills_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
    for tech, color in [
        ("🐍  Python 3.11", "#00c9a7"),
        ("🖥  PyQt6",        "#845ec2"),
        ("🗃  SQLite",        "#f77f00"),
        ("📊  Plotly/Dash",  "#0096c7"),
        ("📑  openpyxl",     "#64748b"),
    ]:
        pill = QLabel(tech)
        pill.setStyleSheet(f"""
            background-color: {color}22;
            color: {color};
            border: 1px solid {color}55;
            border-radius: 20px;
            padding: 5px 14px;
            font-size: 11px;
            font-weight: 600;
        """)
        pills_row.addWidget(pill)
    pills_row.addStretch()
    card_layout.addLayout(pills_row)

    outer.addWidget(card)
    outer.addStretch()
    return page
