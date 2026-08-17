from pathlib import Path

PATH = Path("gui/main_window.py")
text = PATH.read_text(encoding="utf-8-sig")

call_marker = '''        self.apply_style()\n\n        # ====================================================\n        # START\n'''

call_insert = '''        self.apply_style()\n        self.apply_bright_theme()\n\n        # ====================================================\n        # START\n'''

if "self.apply_bright_theme()" not in text:
    if text.count(call_marker) != 1:
        raise RuntimeError(
            f"STYLE marker niet uniek: {text.count(call_marker)}"
        )
    text = text.replace(call_marker, call_insert, 1)

method_marker = '''    # ========================================================\n    # CREATE NAV BUTTON\n'''

method = r'''    # ========================================================
    # BRIGHT THEME
    # ========================================================

    def apply_bright_theme(self):

        # Clear page-local stylesheets so one coherent theme controls
        # the complete application instead of mixing old dark themes.
        roots = [
            self.home_page,
            self.library_page,
            self.detail_page,
            self.discogs_page,
            self.player_bar,
        ]

        for root in roots:

            root.setStyleSheet("")

            for widget in root.findChildren(QWidget):
                widget.setStyleSheet("")

        # Semantic object names.
        for button, name in [
            (self.detail_page.back_button, "detailBack"),
            (self.detail_page.previous_button, "detailPrevious"),
            (self.detail_page.next_button, "detailNext"),
            (self.detail_page.edit_button, "detailEdit"),
            (self.detail_page.checked_button, "checkedButton"),
            (self.library_page.all_button, "filterAll"),
            (self.library_page.todo_button, "filterTodo"),
            (self.library_page.checked_button, "filterChecked"),
        ]:
            button.setObjectName(name)

        if hasattr(self.detail_page, "next_todo_button"):
            self.detail_page.next_todo_button.setObjectName(
                "nextTodoButton"
            )

        if hasattr(self.detail_page, "review_checklist"):
            self.detail_page.review_checklist.setObjectName(
                "reviewChecklist"
            )

        self.library_page.table.setObjectName(
            "releaseTable"
        )

        self.setStyleSheet(
            """
            QWidget {
                background-color: #f6f2f8;
                color: #302a35;
                font-family: Segoe UI;
            }

            QWidget#sidebar {
                background-color: #eee8f3;
                border-right: 1px solid #d9d0df;
            }

            QWidget#rightContainer,
            QWidget#pageStack,
            QWidget#homePage {
                background-color: #f8f6fa;
            }

            QWidget#topBar {
                background-color: #ffffff;
                border-bottom: 1px solid #ddd5e4;
            }

            QLabel#brandSmall,
            QLabel#navigationLabel,
            QLabel#sidebarFooter,
            QLabel#heroSubtitle,
            QLabel#sectionDescription,
            QLabel#dashboardLabel,
            QLabel#statusText {
                color: #756d7d;
                background: transparent;
            }

            QLabel#brandTitle,
            QLabel#topPageTitle,
            QLabel#heroTitle,
            QLabel#sectionTitle,
            QLabel#dashboardNumber,
            QLabel#navText {
                color: #302a35;
                background: transparent;
            }

            QLabel#brandVersion,
            QLabel#dashboardNumberAccent {
                color: #c23d82;
                background: transparent;
            }

            QLabel#collectionBadge {
                background-color: #fae7f1;
                color: #ad326f;
                border: 1px solid #e2bfd1;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #ffffff;
                color: #3a3340;
                border: 1px solid #d3c9db;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #faedf4;
                color: #a83270;
                border: 1px solid #d7a6bc;
            }

            QPushButton:pressed {
                background-color: #c23d82;
                color: #ffffff;
            }

            QPushButton:disabled {
                background-color: #eeeaf1;
                color: #a9a2ad;
                border: 1px solid #ddd7e2;
            }

            QPushButton#navButton {
                background-color: transparent;
                color: #5f5766;
                border: 1px solid transparent;
                text-align: left;
            }

            QPushButton#navButton:hover {
                background-color: #f8edf4;
                color: #8f2b65;
                border: 1px solid #e0c7d6;
            }

            QPushButton#navButton[active="true"] {
                background-color: #f7deeb;
                color: #9c2e6a;
                border: 1px solid #deb1c8;
            }

            QLabel#navIcon {
                background: transparent;
                color: #7c7482;
            }

            QPushButton#navButton[active="true"] QLabel#navIcon {
                color: #c23d82;
            }

            QLineEdit,
            QTextEdit {
                background-color: #ffffff;
                color: #302a35;
                border: 1px solid #cec5d5;
                border-radius: 7px;
                padding: 8px 10px;
                selection-background-color: #e7b5cd;
                selection-color: #302a35;
            }

            QLineEdit:focus,
            QTextEdit:focus {
                border: 1px solid #c23d82;
            }

            QGroupBox {
                background-color: #ffffff;
                color: #8f2b65;
                border: 1px solid #ddd3e2;
                border-radius: 10px;
            }

            QFrame#dashboardCard,
            QFrame#dashboardSection,
            QFrame#statusPanel {
                background-color: #ffffff;
                border: 1px solid #ddd5e4;
                border-radius: 10px;
            }

            QTableWidget#releaseTable {
                background-color: #ffffff;
                alternate-background-color: #f8f5fa;
                color: #302a35;
                gridline-color: #e1dbe5;
                border: 1px solid #d9d1df;
                selection-background-color: #ead4e0;
                selection-color: #302a35;
            }

            QTableWidget#releaseTable::item {
                padding: 6px;
                border: none;
            }

            QHeaderView::section {
                background-color: #eee9f2;
                color: #4c4552;
                padding: 9px;
                border: none;
                border-right: 1px solid #ddd5e4;
                border-bottom: 1px solid #ddd5e4;
                font-weight: bold;
            }

            QPushButton#checkedButton {
                background-color: #dff3e3;
                color: #35613e;
                border: 1px solid #8fc39a;
            }

            QPushButton#checkedButton:hover {
                background-color: #c9e8cf;
                color: #2d5a36;
            }

            QPushButton#checkedButton:pressed {
                background-color: #b7dfbf;
            }

            QLabel#reviewChecklist {
                background-color: #fff9fc;
                color: #4b4350;
                border: 1px solid #ddd1df;
                border-radius: 8px;
                padding: 10px 12px;
                font-weight: 600;
            }

            QScrollBar:vertical {
                background-color: #eeeaf1;
                width: 10px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background-color: #c9becf;
                border-radius: 5px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #c23d82;
            }
            """
        )

'''

if "def apply_bright_theme(self):" not in text:
    if text.count(method_marker) != 1:
        raise RuntimeError(
            f"CREATE NAV marker niet uniek: {text.count(method_marker)}"
        )
    text = text.replace(method_marker, method + method_marker, 1)

PATH.write_text(text, encoding="utf-8-sig")
print("ECHT LICHT THEMA TOEGEVOEGD")
