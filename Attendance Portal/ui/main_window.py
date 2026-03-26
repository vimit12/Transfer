# ======================
# ui/main_window.py — MainWindow with premium sidebar
# ======================
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QStackedWidget, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

from config import APP_NAME, VERSION, DB_PATH
from core.db import initialize_database
from ui.themes import DARK_THEME, LIGHT_THEME


# ─────────────────────────────────────────────────────────────────────────────
# Background worker: initialise DB without blocking the main thread
# ─────────────────────────────────────────────────────────────────────────────
class _DBInitWorker(QThread):
    finished = pyqtSignal(object, list)

    def __init__(self, db_path: str):
        super().__init__()
        self._db_path = db_path

    def run(self):
        conn, tables = initialize_database(self._db_path)
        self.finished.emit(conn, tables)


# ─────────────────────────────────────────────────────────────────────────────
# MainWindow
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}")
        self.setMinimumSize(1280, 760)

        # State
        self.db_connection = None
        self.all_tables_name: list = []
        self.current_table: str = ""
        self.current_theme_idx: int = 0

        # Home-page data
        self.df = None
        self.raw_category_list = []
        self.categories = {}
        self.name_mapping = {}
        self.name_order_list = []
        self.HOLIDAY_LIST = []
        self.selected_month = ""
        self.selected_year = ""

        # Spreadsheet page state
        self.spreadsheet_df = None
        self.spreadsheet_table_name = ""
        self.column_defs = {}

        # Lazy page tracking
        self._page_built = [False] * 5
        self._page_factories = []

        self.init_ui()
        self._start_db_worker()

    # ── DB init ──────────────────────────────────────────────────────────────
    def _start_db_worker(self):
        self._db_worker = _DBInitWorker(DB_PATH)
        self._db_worker.finished.connect(self._on_db_ready)
        self._db_worker.start()

    def _on_db_ready(self, conn, tables):
        self.db_connection = conn
        self.all_tables_name = tables
        if hasattr(self, 'db_table_combo') and tables:
            self.db_table_combo.clear()
            self.db_table_combo.addItems(tables)

    # ── UI Construction ───────────────────────────────────────────────────────
    def init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        root_layout = QHBoxLayout(container)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # ── Build Sidebar ─────────────────────────────────────────────────────
        sidebar = self._build_sidebar()

        # ── Main content area ─────────────────────────────────────────────────
        self.stacked = QStackedWidget()
        self.stacked.setContentsMargins(0, 0, 0, 0)
        for _ in range(5):
            self.stacked.addWidget(QWidget())

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stacked, 1)

        self._page_factories = [
            self._build_home_page,
            self._build_database_page,
            self._build_load_data_page,
            self._build_spreadsheet_page,
            self._build_about_page,
        ]

        self.setStyleSheet(DARK_THEME)
        self.switch_page(0)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo / Brand area ─────────────────────────────────────────────
        brand = QWidget()
        brand.setFixedHeight(90)
        brand.setStyleSheet("background: transparent;")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(20, 18, 20, 10)
        brand_layout.setSpacing(2)

        app_name_lbl = QLabel("⚡ AttendanceBI")
        app_name_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.3px;
        """)

        ver_lbl = QLabel(f"v{VERSION}  •  Hitachi Digital")
        ver_lbl.setStyleSheet("""
            color: rgba(148,163,184,0.7);
            font-size: 10px;
            font-weight: 400;
        """)

        brand_layout.addWidget(app_name_lbl)
        brand_layout.addWidget(ver_lbl)
        layout.addWidget(brand)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: rgba(255,255,255,0.06);")
        layout.addWidget(div)
        layout.addSpacing(12)

        # ── Nav items ────────────────────────────────────────────────────
        nav_items = [
            ("🏠", "Home",          0),
            ("🗄️", "Database",      1),
            ("📥", "Load Dataset",  2),
            ("📊", "Spreadsheet",   3),
            ("ℹ️", "About",         4),
        ]
        self.nav_buttons: list[QPushButton] = []

        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 0, 12, 0)
        nav_layout.setSpacing(4)

        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addWidget(nav_container)
        layout.addStretch()

        # Divider
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background: rgba(255,255,255,0.06);")
        layout.addWidget(div2)

        # ── Footer: theme toggle ─────────────────────────────────────────
        footer = QWidget()
        footer.setFixedHeight(70)
        footer.setStyleSheet("background: transparent;")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(12, 10, 12, 10)

        self.theme_btn = QPushButton("🌙  Switch to Light Mode")
        self.theme_btn.setObjectName("theme_btn")
        self.theme_btn.setFixedHeight(38)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.cycle_theme)
        footer_layout.addWidget(self.theme_btn)
        layout.addWidget(footer)

        return sidebar

    # ── Lazy page loading ─────────────────────────────────────────────────────
    def switch_page(self, index: int):
        if not self._page_built[index]:
            page = self._page_factories[index]()
            self.stacked.removeWidget(self.stacked.widget(index))
            self.stacked.insertWidget(index, page)
            self._page_built[index] = True

        self.stacked.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    # ── Page factories ────────────────────────────────────────────────────────
    def _build_home_page(self) -> QWidget:
        from ui.pages.home_page import create_home_page
        return create_home_page(self)

    def _build_database_page(self) -> QWidget:
        from ui.pages.database_page import create_database_page, show_table_contents
        page = create_database_page(self)
        if self.all_tables_name and hasattr(self, 'db_table_combo'):
            self.db_table_combo.addItems(self.all_tables_name)
            if self.all_tables_name:
                show_table_contents(self, self.all_tables_name[0])
        elif not self.all_tables_name:
            def _try_populate():
                if self.all_tables_name and hasattr(self, 'db_table_combo'):
                    self.db_table_combo.addItems(self.all_tables_name)
                    show_table_contents(self, self.all_tables_name[0])
                else:
                    QTimer.singleShot(500, _try_populate)
            QTimer.singleShot(500, _try_populate)
        return page

    def _build_load_data_page(self) -> QWidget:
        from ui.pages.load_data_page import create_load_data_page
        return create_load_data_page(self)

    def _build_spreadsheet_page(self) -> QWidget:
        from ui.pages.spreadsheet_page import create_spreadsheet_page
        return create_spreadsheet_page(self)

    def _build_about_page(self) -> QWidget:
        from ui.pages.about_page import create_about_page
        return create_about_page()

    # ── Theme management ──────────────────────────────────────────────────────
    def cycle_theme(self):
        self.current_theme_idx = (self.current_theme_idx + 1) % 2
        self._apply_theme()

    def _apply_theme(self):
        if self.current_theme_idx == 0:
            self.setStyleSheet(DARK_THEME)
            self.theme_btn.setText("🌙  Switch to Light Mode")
        else:
            self.setStyleSheet(LIGHT_THEME)
            self.theme_btn.setText("☀️  Switch to Dark Mode")

    # ── Public helpers ────────────────────────────────────────────────────────
    def initialize_database(self):
        self._start_db_worker()

    def load_holidays_to_db(self):
        if self._page_built[0]:
            from ui.pages.home_page import load_holidays_to_db
            load_holidays_to_db(self)

    def handle_custom_file_upload(self):
        if self._page_built[3]:
            from ui.pages.spreadsheet_page import handle_custom_file_upload
            handle_custom_file_upload(self)

    def show_message(self, text: str, msg_type: str = "info", timeout: int = 5000):
        """Proxy for pages that call window.show_message()."""
        if self._page_built[0] and hasattr(self, 'msg_label'):
            from ui.pages.home_page import show_message
            show_message(self, text, msg_type, timeout)

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    def closeEvent(self, event):
        if self.db_connection:
            self.db_connection.close()
        event.accept()
