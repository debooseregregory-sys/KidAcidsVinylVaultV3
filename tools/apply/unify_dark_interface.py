from pathlib import Path

PATH = Path("gui/main_window.py")
text = PATH.read_text(encoding="utf-8-sig")

marker = '''        self.apply_style()\n\n        # ====================================================\n        # START\n'''

insert = '''        self.apply_style()\n\n        # ====================================================\n        # UNIFY CHILD WIDGET STYLES\n        # ====================================================\n\n        protected = {\n            "review_checklist",\n            "checked_button",\n        }\n\n        def clear_local_styles(widget):\n            if widget.objectName() not in protected:\n                widget.setStyleSheet("")\n\n            for child in widget.findChildren(QWidget):\n                if child.objectName() not in protected:\n                    child.setStyleSheet("")\n\n        clear_local_styles(self.library_page)\n        clear_local_styles(self.detail_page)\n        clear_local_styles(self.discogs_page)\n\n        # Re-apply the global theme after removing page-local styles.\n        self.apply_style()\n\n        # ====================================================\n        # START\n'''

if text.count(marker) != 1:
    raise RuntimeError(
        f"START marker verwacht 1 keer, gevonden {text.count(marker)}"
    )

text = text.replace(marker, insert, 1)

style_marker = '''            QWidget {\n                background-color: #0b0b0f;\n                color: #f2f2f5;\n                font-family: "Segoe UI";\n            }\n'''

style_insert = '''            QWidget {\n                background-color: #09090c;\n                color: #f5f5f7;\n                font-family: "Segoe UI";\n                font-size: 15px;\n            }\n\n            QLabel {\n                color: #f5f5f7;\n                font-size: 15px;\n            }\n\n            QGroupBox {\n                background-color: #111116;\n                color: #f5f5f7;\n                border: 1px solid #2b2b34;\n                border-radius: 10px;\n                margin-top: 10px;\n                padding: 12px;\n            }\n\n            QScrollArea, QScrollArea > QWidget > QWidget {\n                background-color: #09090c;\n                border: none;\n            }\n\n            QFrame {\n                background-color: #111116;\n                color: #f5f5f7;\n            }\n'''

if style_marker not in text:
    raise RuntimeError("Global QWidget stylesheet marker niet gevonden")

text = text.replace(style_marker, style_insert, 1)

text = text.replace(
    'icon_label.setFixedWidth(\n            24\n        )',
    'icon_label.setFixedWidth(\n            42\n        )'
)

text = text.replace(
    'QLabel#navIcon {\n                background: transparent;\n                color: #777783;\n                font-size: 18px;',
    'QLabel#navIcon {\n                background: transparent;\n                color: #c7c7cf;\n                font-size: 30px;'
)

text = text.replace(
    'QLabel#navText {\n                background: transparent;\n                color: inherit;\n                font-size: 13px;',
    'QLabel#navText {\n                background: transparent;\n                color: #f5f5f7;\n                font-size: 16px;'
)

text = text.replace(
    'background-color: #271522;',
    'background-color: #18181e;'
)
text = text.replace(
    'border: 1px solid #5d2947;',
    'border: 1px solid #d84b91;'
)

text = text.replace('background-color: #0b0b0f;', 'background-color: #09090c;')
text = text.replace('background-color: #111116;', 'background-color: #101014;')
text = text.replace('background-color: #0f0f14;', 'background-color: #0d0d11;')

PATH.write_text(text, encoding="utf-8-sig")
print("UNIFORME ZWARTE INTERFACE TOEGEVOEGD")
