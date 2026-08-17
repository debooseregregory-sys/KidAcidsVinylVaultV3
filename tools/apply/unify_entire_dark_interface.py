from pathlib import Path

MAIN = Path("gui/main_window.py")

text = MAIN.read_text(encoding="utf-8-sig")

# Insert the global-theme call after the existing main-window stylesheet call.
call_marker = "        self.apply_style()\n"
call_insert = "        self.apply_style()\n\n        self.apply_uniform_dark_theme()\n"

if "def apply_uniform_dark_theme(self):" not in text:
    if text.count(call_marker) != 1:
        raise RuntimeError(
            f"self.apply_style() verwacht 1 keer, gevonden {text.count(call_marker)}"
        )
    text = text.replace(call_marker, call_insert, 1)

# Insert the new method immediately before CREATE NAV BUTTON.
method_marker = "    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n"
method = r'''    # ========================================================
    # UNIFORM DARK THEME
    # ========================================================

    def apply_uniform_dark_theme(self):

        from PySide6.QtWidgets import QApplication

        # Remove local page styles so the application theme is authoritative.
        protected = {
            "review_checklist",
            "checked_button",
        }

        for page in (
            self.library_page,
            self.detail_page,
            self.discogs_page,
        ):
            page.setStyleSheet("")
            for child in page.findChildren(QWidget):
                if child.objectName() not in protected:
                    child.setStyleSheet("")

        app = QApplication.instance()

        if app is None:
            return

        app.setStyleSheet(
            r"""
            * {
                font-family: "Segoe UI";
                font-size: 15px;
            }

            QMainWindow, QWidget,
            QWidget#centralWidget,
            QWidget#rightContainer,
            QStackedWidget#pageStack,
            QWidget#homePage {
                background-color: #09090c;
                color: #f5f5f7;
            }

            QWidget#sidebar {
                background-color: #0d0d10;
                border-right: 1px solid #262630;
            }

            QWidget#topBar {
                background-color: #0b0b0e;
                border-bottom: 1px solid #262630;
            }

            QLabel {
                background: transparent;
                color: #f5f5f7;
            }

            QLabel#brandSmall,
            QLabel#navigationLabel,
            QLabel#sidebarFooter {
                color: #9b98a4;
            }

            QLabel#brandTitle {
                color: #ffffff;
                font-size: 28px;
                font-weight: 800;
            }

            QLabel#brandVersion {
                color: #d84b91;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#topPageTitle,
            QLabel#heroTitle,
            QLabel#sectionTitle {
                color: #ffffff;
            }

            QLabel#topPageTitle {
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#heroTitle {
                font-size: 34px;
                font-weight: 800;
            }

            QLabel#heroSubtitle,
            QLabel#sectionDescription,
            QLabel#dashboardLabel,
            QLabel#statusText {
                color: #a8a5af;
            }

            QLabel#navIcon {
                color: #c7c5ce;
                font-size: 32px;
                min-width: 42px;
            }

            QLabel#navText {
                color: #f2f2f5;
                font-size: 16px;
                font-weight: 600;
            }

            QPushButton#navButton {
                background-color: #121217;
                color: #f2f2f5;
                border: 1px solid #24242c;
                border-radius: 10px;
                min-height: 58px;
                text-align: left;
            }

            QPushButton#navButton:hover {
                background-color: #1a1a21;
                border: 1px solid #4b3a45;
            }

            QPushButton#navButton[active="true"] {
                background-color: #17171d;
                border: 1px solid #d84b91;
            }

            QPushButton#navButton[active="true"] QLabel#navIcon {
                color: #e05299;
            }

            QLineEdit,
            QTextEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                background-color: #111116;
                color: #f5f5f7;
                border: 1px solid #34343d;
                border-radius: 8px;
                padding: 9px 11px;
                selection-background-color: #6d2f4f;
                selection-color: #ffffff;
            }

            QLineEdit:focus,
            QTextEdit:focus,
            QComboBox:focus {
                border: 1px solid #d84b91;
            }

            QPushButton,
            QPushButton#sectionButton {
                background-color: #15151b;
                color: #f3f3f6;
                border: 1px solid #34343d;
                border-radius: 8px;
                padding: 9px 15px;
                font-weight: 700;
            }

            QPushButton:hover,
            QPushButton#sectionButton:hover {
                background-color: #1e1e26;
                border: 1px solid #d84b91;
            }

            QPushButton:pressed,
            QPushButton#sectionButton:pressed {
                background-color: #2a1723;
                border: 1px solid #d84b91;
            }

            QTableWidget {
                background-color: #0f0f13;
                alternate-background-color: #15151b;
                color: #f5f5f7;
                gridline-color: #2a2a32;
                border: 1px solid #2a2a32;
                selection-background-color: #303039;
                selection-color: #ffffff;
                font-size: 15px;
            }

            QTableWidget::item {
                padding: 8px;
                border: none;
            }

            QHeaderView::section {
                background-color: #18181e;
                color: #ffffff;
                padding: 10px;
                border: none;
                border-right: 1px solid #292932;
                border-bottom: 1px solid #292932;
                font-weight: 700;
            }

            QGroupBox,
            QFrame#dashboardCard,
            QFrame#dashboardSection {
                background-color: #111116;
                color: #f5f5f7;
                border: 1px solid #292932;
                border-radius: 10px;
            }

            QScrollArea,
            QScrollArea > QWidget > QWidget {
                background-color: #09090c;
                border: none;
            }

            QScrollBar:vertical {
                background: #101014;
                width: 11px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: #3a3942;
                border-radius: 5px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background: #d84b91;
            }
            """
        )

        # Re-apply the semantic checklist colours after clearing local styles.
        if hasattr(self.detail_page, "review_checklist"):
            self.detail_page.review_checklist.setStyleSheet(
                """
                QLabel {
                    background-color: #111116;
                    color: #f5f5f7;
                    border: 1px solid #34343d;
                    border-radius: 8px;
                    padding: 10px 12px;
                    font-size: 14px;
                    font-weight: 700;
                }
                """
            )

        if hasattr(self.detail_page, "checked_button"):
            self.detail_page.checked_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #17321f;
                    color: #d9f5df;
                    border: 1px solid #3f8a50;
                    border-radius: 8px;
                    padding: 9px 15px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #204829;
                    border: 1px solid #63b873;
                }
                """
            )

'''

if "def apply_uniform_dark_theme(self):" not in text:
    if text.count(method_marker) != 1:
        raise RuntimeError(
            f"CREATE NAV BUTTON marker verwacht 1 keer, gevonden {text.count(method_marker)}"
        )
    text = text.replace(method_marker, method + method_marker, 1)

MAIN.write_text(text, encoding="utf-8-sig")
print("UNIFORME ZWARTE THEME GEÏNSTALLEERD")
'''
