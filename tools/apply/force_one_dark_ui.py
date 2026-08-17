from pathlib import Path

PATH = Path("gui/main_window.py")
text = PATH.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# Add a final dark-page normalization call immediately after
# the existing main-window stylesheet is applied.
# ------------------------------------------------------------
apply_marker = '''        self.apply_style()\n\n        # ====================================================\n        # START\n'''
apply_insert = '''        self.apply_style()\n        self.apply_dark_page_style()\n\n        # ====================================================\n        # START\n'''

if "self.apply_dark_page_style()" not in text:
    if text.count(apply_marker) != 1:
        raise RuntimeError(
            f"apply_style marker verwacht 1 keer, gevonden {text.count(apply_marker)}"
        )
    text = text.replace(apply_marker, apply_insert, 1)

# ------------------------------------------------------------
# Insert the final page-wide dark theme method.
# ------------------------------------------------------------
method_marker = '''    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n'''
method_insert = '''    # ========================================================\n    # FINAL DARK PAGE STYLE\n    # ========================================================\n\n    def apply_dark_page_style(self):\n\n        protected_names = {\n            "review_checklist",\n            "checked_button",\n        }\n\n        pages = [\n            self.library_page,\n            self.detail_page,\n            self.discogs_page,\n        ]\n\n        for page in pages:\n\n            page.setStyleSheet("")\n\n            for child in page.findChildren(QWidget):\n\n                if child.objectName() in protected_names:\n                    continue\n\n                child.setStyleSheet("")\n\n        page_style = """\n            QWidget {\n                background-color: #09090c;\n                color: #f4f4f6;\n                font-family: \"Segoe UI\";\n                font-size: 15px;\n            }\n\n            QLabel {\n                background: transparent;\n                color: #f4f4f6;\n                font-size: 15px;\n            }\n\n            QGroupBox {\n                background-color: #111116;\n                color: #f4f4f6;\n                border: 1px solid #2b2b34;\n                border-radius: 10px;\n                margin-top: 10px;\n                padding: 12px;\n            }\n\n            QLineEdit, QTextEdit {\n                background-color: #141419;\n                color: #ffffff;\n                border: 1px solid #35353f;\n                border-radius: 7px;\n                padding: 9px 11px;\n                selection-background-color: #703552;\n                selection-color: #ffffff;\n            }\n\n            QLineEdit:focus, QTextEdit:focus {\n                border: 1px solid #d84b91;\n            }\n\n            QPushButton {\n                background-color: #17171d;\n                color: #f4f4f6;\n                border: 1px solid #34343d;\n                border-radius: 7px;\n                padding: 9px 15px;\n                font-size: 14px;\n                font-weight: 600;\n            }\n\n            QPushButton:hover {\n                background-color: #202027;\n                border: 1px solid #d84b91;\n            }\n\n            QPushButton:pressed {\n                background-color: #2b1a25;\n            }\n\n            QPushButton:disabled {\n                background-color: #111116;\n                color: #5e5e67;\n                border: 1px solid #24242c;\n            }\n\n            QScrollArea, QScrollArea > QWidget > QWidget {\n                background-color: #09090c;\n                border: none;\n            }\n\n            QFrame {\n                background-color: #111116;\n                color: #f4f4f6;\n            }\n\n            QScrollBar:vertical {\n                background: #101014;\n                width: 11px;\n                border: none;\n            }\n\n            QScrollBar::handle:vertical {\n                background: #393943;\n                border-radius: 5px;\n                min-height: 40px;\n            }\n\n            QScrollBar::handle:vertical:hover {\n                background: #d84b91;\n            }\n\n            QScrollBar:horizontal {\n                background: #101014;\n                height: 11px;\n                border: none;\n            }\n\n            QScrollBar::handle:horizontal {\n                background: #393943;\n                border-radius: 5px;\n                min-width: 40px;\n            }\n\n            QScrollBar::handle:horizontal:hover {\n                background: #d84b91;\n            }\n        """\n\n        for page in pages:\n            page.setStyleSheet(page_style)\n\n        # Ensure the protected review controls retain their semantic colours.\n        if hasattr(self.detail_page, "checked_button"):\n            self.detail_page.checked_button.setStyleSheet(\n                """\n                QPushButton {\n                    background-color: #19331f;\n                    color: #d8f5de;\n                    border: 1px solid #3f7b4b;\n                    border-radius: 7px;\n                    padding: 9px 15px;\n                    font-weight: 700;\n                }\n                QPushButton:hover {\n                    background-color: #23472c;\n                    border: 1px solid #70c17d;\n                }\n                """\n            )\n\n        if hasattr(self.detail_page, "review_checklist"):\n            self.detail_page.review_checklist.setStyleSheet(\n                """\n                QLabel {\n                    background-color: #111116;\n                    color: #f4f4f6;\n                    border: 1px solid #2b2b34;\n                    border-radius: 8px;\n                    padding: 10px 12px;\n                    font-size: 14px;\n                    font-weight: 700;\n                }\n                """\n            )\n\n    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n'''

if "def apply_dark_page_style(self):" not in text:
    if text.count(method_marker) != 1:
        raise RuntimeError(
            f"create_nav_button marker verwacht 1 keer, gevonden {text.count(method_marker)}"
        )
    text = text.replace(method_marker, method_insert, 1)

# ------------------------------------------------------------
# Make sidebar icon controls genuinely larger and give them
# a little more room.
# ------------------------------------------------------------
text = text.replace(
    'button.setMinimumHeight(\n            48\n        )',
    'button.setMinimumHeight(\n            56\n        )',
    1,
)

text = text.replace(
    'icon_label.setFixedWidth(\n            24\n        )',
    'icon_label.setFixedWidth(\n            42\n        )',
    1,
)

text = text.replace(
    'font-size: 18px;\n                font-weight: bold;',
    'font-size: 30px;\n                font-weight: bold;',
    1,
)

text = text.replace(
    'self.home_button = self.create_nav_button(\n            "⌂",\n            "Dashboard"\n        )',
    'self.home_button = self.create_nav_button(\n            "⌂",\n            "Dashboard"\n        )',
    1,
)

PATH.write_text(text, encoding="utf-8-sig")
print("UNIFORME ZWARTE PAGINA-STIJL TOEGEVOEGD")
