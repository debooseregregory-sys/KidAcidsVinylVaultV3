from pathlib import Path

PATH = Path("gui/main_window.py")
text = PATH.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# Clear page-local styles after the complete UI has been built.
# This lets the central MainWindow stylesheet control the whole
# Release Library / Release Detail / Discogs surface.
# ------------------------------------------------------------

marker = '''        self.apply_style()\n\n        # ====================================================\n        # START\n        # ====================================================\n'''

replacement = '''        self.apply_style()\n\n        # ====================================================\n        # USE CENTRAL DARK THEME FOR ALL PAGES\n        # ====================================================\n\n        self.library_page.setStyleSheet(\n            ""\n        )\n\n        self.detail_page.setStyleSheet(\n            ""\n        )\n\n        self.discogs_page.setStyleSheet(\n            ""\n        )\n\n        # Re-apply the central stylesheet after clearing the\n        # page-local stylesheets.\n        self.apply_style()\n\n        # ====================================================\n        # START\n        # ====================================================\n'''

if text.count(marker) != 1:
    raise RuntimeError(
        f"UI marker verwacht 1 keer, gevonden {text.count(marker)}"
    )

text = text.replace(
    marker,
    replacement,
    1
)

# ------------------------------------------------------------
# Make sidebar icons genuinely larger.
# ------------------------------------------------------------

old_width = '''        icon_label.setFixedWidth(\n            24\n        )\n'''
new_width = '''        icon_label.setFixedWidth(\n            42\n        )\n\n        icon_label.setStyleSheet(\n            """\n            QLabel {\n                background: transparent;\n                color: #d84b91;\n                font-size: 30px;\n                font-weight: 800;\n            }\n            """\n        )\n'''

if text.count(old_width) != 1:
    raise RuntimeError(
        f"icon width marker verwacht 1 keer, gevonden {text.count(old_width)}"
    )

text = text.replace(
    old_width,
    new_width,
    1
)

old_text_label = '''        text_label.setObjectName(\n            "navText"\n        )\n'''
new_text_label = '''        text_label.setObjectName(\n            "navText"\n        )\n\n        text_label.setStyleSheet(\n            """\n            QLabel {\n                background: transparent;\n                color: #f5f5f7;\n                font-size: 16px;\n                font-weight: 700;\n            }\n            """\n        )\n'''

if text.count(old_text_label) != 1:
    raise RuntimeError(
        f"nav text marker verwacht 1 keer, gevonden {text.count(old_text_label)}"
    )

text = text.replace(
    old_text_label,
    new_text_label,
    1
)

# ------------------------------------------------------------
# Active navigation remains dark. Pink is accent only.
# ------------------------------------------------------------

text = text.replace(
    'background-color: #271522;',
    'background-color: #18181f;'
)

text = text.replace(
    'border: 1px solid #5d2947;',
    'border: 1px solid #d84b91;'
)

PATH.write_text(text, encoding="utf-8-sig")
print("PAGINA-STYLES GEUNIFORMEERD + SIDEBAR ICONEN VERGROOT")
