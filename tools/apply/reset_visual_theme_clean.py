from pathlib import Path

PATH = Path("gui/main_window.py")
text = PATH.read_text(encoding="utf-8-sig")

# Add a runtime cleanup method and call it after all child pages are created.
marker = "        self.apply_style()\n\n        # ====================================================\n        # START\n"
insert = '''        self.apply_style()\n\n        # ====================================================\n        # CLEAN PAGE-LOCAL STYLES\n        # ====================================================\n\n        self._reset_child_page_styles()\n        self.apply_style()\n\n        # ====================================================\n        # START\n'''
if "def _reset_child_page_styles(self):" not in text:
    if marker not in text:
        raise RuntimeError("STYLE/START marker niet gevonden")
    text = text.replace(marker, insert, 1)

method_marker = "    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n"
method_insert = '''    # ========================================================\n    # RESET CHILD PAGE STYLES\n    # ========================================================\n\n    def _reset_child_page_styles(self):\n\n        protected = {\n            "review_checklist",\n            "checked_button",\n        }\n\n        def clear(widget):\n            if widget.objectName() not in protected:\n                widget.setStyleSheet("")\n\n            for child in widget.findChildren(QWidget):\n                if child.objectName() not in protected:\n                    child.setStyleSheet("")\n\n        clear(self.library_page)\n        clear(self.detail_page)\n        clear(self.discogs_page)\n\n    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n'''
if "def _reset_child_page_styles(self):" not in text:
    if method_marker not in text:
        raise RuntimeError("CREATE NAV BUTTON marker niet gevonden")
    text = text.replace(method_marker, method_insert, 1)

# Make sidebar controls genuinely larger.
text = text.replace("icon_label.setFixedWidth(\n            24\n        )", "icon_label.setFixedWidth(\n            42\n        )")
text = text.replace("QLabel#navIcon {\n                background: transparent;\n                color: #777783;\n                font-size: 18px;", "QLabel#navIcon {\n                background: transparent;\n                color: #c9c9d1;\n                font-size: 30px;")
text = text.replace("QLabel#navText {\n                background: transparent;\n                color: inherit;\n                font-size: 13px;", "QLabel#navText {\n                background: transparent;\n                color: #f5f5f7;\n                font-size: 16px;")

# Ensure the global surfaces are black/charcoal and active nav is not pink-filled.
text = text.replace("background-color: #0b0b0f;", "background-color: #09090c;")
text = text.replace("background-color: #0f0f14;", "background-color: #0d0d11;")
text = text.replace("background-color: #111116;", "background-color: #101014;")
text = text.replace("background-color: #271522;", "background-color: #19191f;")
text = text.replace("background-color: #f8e3ef;", "background-color: #19191f;")

PATH.write_text(text, encoding="utf-8-sig")
print("VISUELE STIJL OPNIEUW INGESTELD")
