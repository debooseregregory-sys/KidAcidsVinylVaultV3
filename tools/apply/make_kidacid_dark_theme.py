from pathlib import Path
import re

PATH = Path("gui/main_window.py")

text = PATH.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# Window sizing: comfortable on smaller screens and still fluid
# when maximized.
# ------------------------------------------------------------
text = text.replace(
    '''        self.setMinimumSize(\n            1200,\n            760\n        )\n\n        self.resize(\n            1500,\n            900\n        )\n''',
    '''        self.setMinimumSize(\n            1100,\n            700\n        )\n\n        self.resize(\n            1500,\n            900\n        )\n''',
    1,
)

# ------------------------------------------------------------
# Sidebar symbols: cleaner, stronger visual hierarchy.
# ------------------------------------------------------------
text = text.replace('self.create_nav_button(\n            "⌂",\n            "Dashboard"', 'self.create_nav_button(\n            "⌂",\n            "Dashboard"', 1)
text = text.replace('self.create_nav_button(\n            "▣",\n            "Release Library"', 'self.create_nav_button(\n            "▦",\n            "Release Library"', 1)
text = text.replace('self.create_nav_button(\n            "◈",\n            "Discogs Import"', 'self.create_nav_button(\n            "◉",\n            "Discogs Import"', 1)

# ------------------------------------------------------------
# Replace the complete main stylesheet.
# ------------------------------------------------------------
start = text.find('    def apply_style(\n        self\n    ):\n')
if start < 0:
    raise RuntimeError("apply_style methode niet gevonden")

end = text.find('\n\n# ============================================================\n# START\n', start)
if end < 0:
    raise RuntimeError("einde van apply_style niet gevonden")

method = r'''    def apply_style(
        self
    ):

        self.setStyleSheet(
            """
            /* ==================================================
               KID ACID'S VINYLVAULT - DARK MODERN THEME
               ================================================== */

            QMainWindow,
            QWidget {
                background-color: #09090b;
                color: #f5f5f7;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QWidget#centralWidget,
            QWidget#rightContainer,
            QStackedWidget#pageStack {
                background-color: #09090b;
            }

            /* ==================================================
               SIDEBAR
               ================================================== */

            QWidget#sidebar {
                background-color: #0d0d10;
                border-right: 1px solid #292931;
            }

            QLabel#brandSmall {
                background: transparent;
                color: #b8b8c2;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QLabel#brandTitle {
                background: transparent;
                color: #ffffff;
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#brandVersion {
                background: transparent;
                color: #ff4fa3;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }

            QLabel#navigationLabel {
                background: transparent;
                color: #7e7e8b;
                font-size: 11px;
                font-weight: 700;
                padding-left: 12px;
                letter-spacing: 1.8px;
            }

            QLabel#sidebarFooter {
                background: transparent;
                color: #6f6f79;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                padding-top: 8px;
            }

            QPushButton#navButton {
                background-color: transparent;
                color: #c7c7d0;
                border: 1px solid transparent;
                border-radius: 10px;
                text-align: left;
                min-height: 52px;
                padding: 6px 10px;
                font-size: 15px;
                font-weight: 700;
            }

            QPushButton#navButton:hover {
                background-color: #17131b;
                color: #ffffff;
                border: 1px solid #3b3042;
            }

            QPushButton#navButton[active="true"] {
                background-color: #251226;
                color: #ffffff;
                border: 1px solid #7c2e5c;
            }

            QLabel#navIcon {
                background: transparent;
                color: #a3a3af;
                font-size: 22px;
                font-weight: 800;
            }

            QPushButton#navButton[active="true"] QLabel#navIcon {
                color: #ff4fa3;
            }

            QLabel#navText {
                background: transparent;
                color: inherit;
                font-size: 15px;
                font-weight: 700;
            }

            /* ==================================================
               TOP BAR
               ================================================== */

            QWidget#topBar {
                background-color: #0b0b0e;
                border-bottom: 1px solid #292931;
            }

            QLabel#topPageTitle {
                background: transparent;
                color: #ffffff;
                font-size: 24px;
                font-weight: 800;
            }

            QLabel#collectionBadge {
                background-color: #21121d;
                color: #ff67ad;
                border: 1px solid #6d2b51;
                border-radius: 16px;
                padding: 7px 14px;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            /* ==================================================
               DASHBOARD
               ================================================== */

            QWidget#homePage {
                background-color: #09090b;
            }

            QLabel#heroTitle {
                background: transparent;
                color: #ffffff;
                font-size: 34px;
                font-weight: 800;
            }

            QLabel#heroSubtitle {
                background: transparent;
                color: #a7a7b2;
                font-size: 15px;
            }

            QFrame#dashboardCard,
            QFrame#dashboardSection {
                background-color: #131318;
                border: 1px solid #2d2d36;
                border-radius: 12px;
            }

            QFrame#dashboardCard:hover,
            QFrame#dashboardSection:hover {
                background-color: #17151a;
                border: 1px solid #61354f;
            }

            QLabel#dashboardNumber,
            QLabel#dashboardNumberAccent {
                background: transparent;
                color: #ffffff;
                font-size: 32px;
                font-weight: 800;
            }

            QLabel#dashboardNumberAccent {
                color: #ff4fa3;
            }

            QLabel#dashboardLabel {
                background: transparent;
                color: #92929e;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#sectionTitle {
                background: transparent;
                color: #ffffff;
                font-size: 19px;
                font-weight: 800;
            }

            QLabel#sectionDescription {
                background: transparent;
                color: #a6a6b1;
                font-size: 13px;
            }

            QPushButton#sectionButton {
                background-color: #1c1720;
                color: #ff67ad;
                border: 1px solid #6d2b51;
                border-radius: 8px;
                padding: 9px 15px;
                font-size: 12px;
                font-weight: 800;
            }

            QPushButton#sectionButton:hover {
                background-color: #ff4fa3;
                color: #ffffff;
                border: 1px solid #ff4fa3;
            }

            /* ==================================================
               GENERAL BUTTONS
               ================================================== */

            QPushButton {
                background-color: #17171d;
                color: #f4f4f7;
                border: 1px solid #35353f;
                border-radius: 8px;
                padding: 9px 15px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #241924;
                border: 1px solid #ff4fa3;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #ff4fa3;
                color: #ffffff;
            }

            QPushButton:disabled {
                background-color: #111116;
                color: #666671;
                border: 1px solid #26262d;
            }

            /* ==================================================
               INPUTS
               ================================================== */

            QLineEdit,
            QTextEdit {
                background-color: #121217;
                color: #ffffff;
                border: 1px solid #3a3a44;
                border-radius: 8px;
                padding: 9px 11px;
                font-size: 14px;
                selection-background-color: #7f315a;
                selection-color: #ffffff;
            }

            QLineEdit:focus,
            QTextEdit:focus {
                border: 1px solid #ff4fa3;
            }

            /* ==================================================
               TABLES
               ================================================== */

            QTableWidget {
                background-color: #0f0f13;
                alternate-background-color: #15151b;
                color: #f2f2f5;
                gridline-color: #2c2c34;
                border: 1px solid #2f2f38;
                selection-background-color: #52223e;
                selection-color: #ffffff;
                font-size: 14px;
            }

            QTableWidget::item {
                padding: 7px;
                border: none;
            }

            QHeaderView::section {
                background-color: #19191f;
                color: #ffffff;
                padding: 10px;
                border: none;
                border-right: 1px solid #2c2c34;
                border-bottom: 1px solid #2c2c34;
                font-size: 12px;
                font-weight: 800;
            }

            /* ==================================================
               GROUP BOX / DETAIL VIEW
               ================================================== */

            QGroupBox {
                background-color: #111117;
                color: #ff67ad;
                border: 1px solid #35353f;
                border-radius: 10px;
                margin-top: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: 800;
            }

            QLabel {
                font-size: 14px;
            }

            /* ==================================================
               REVIEW CHECKLIST
               ================================================== */

            QLabel#reviewChecklist,
            QLabel#reviewStatus {
                background-color: #131318;
                color: #f2f2f5;
                border: 1px solid #35353f;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 14px;
                font-weight: 800;
            }

            /* ==================================================
               SCROLLBARS
               ================================================== */

            QScrollBar:vertical {
                background-color: #0f0f13;
                width: 12px;
                border: none;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background-color: #454550;
                border-radius: 6px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #ff4fa3;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background-color: #0f0f13;
                height: 12px;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background-color: #454550;
                border-radius: 6px;
                min-width: 40px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #ff4fa3;
            }
            """
        )
'''

text = text[:start] + method + text[end:]
PATH.write_text(text, encoding="utf-8-sig")
print("KID ACID DARK THEME TOEGEPAST")
