from pathlib import Path

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

# The current page already imports QScrollArea. Replace the direct body layout
# with a scrollable content widget that keeps the original proportions when the
# main window is restored to a narrow size.
old = '''        body.addWidget(card, 1)\n        root.addLayout(body, 1)\n'''
new = '''        body.addWidget(card, 1)\n\n        self.showcase_scroll = QScrollArea()\n        self.showcase_scroll.setWidgetResizable(False)\n        self.showcase_scroll.setHorizontalScrollBarPolicy(\n            Qt.ScrollBarPolicy.ScrollBarAsNeeded\n        )\n        self.showcase_scroll.setVerticalScrollBarPolicy(\n            Qt.ScrollBarPolicy.ScrollBarAsNeeded\n        )\n        self.showcase_scroll.setFrameShape(QFrame.Shape.NoFrame)\n\n        self.showcase_content = QWidget()\n        self.showcase_content.setMinimumWidth(1120)\n        self.showcase_content.setMinimumHeight(620)\n        self.showcase_content.setLayout(body)\n        self.showcase_scroll.setWidget(self.showcase_content)\n        root.addWidget(self.showcase_scroll, 1)\n'''

if old not in text:
    raise SystemExit("Expected body layout block not found")

text = text.replace(old, new, 1)

# Remove any resize handlers from earlier responsive patches. The scroll area
# deliberately avoids forcing children into a smaller width.
start = text.find("    def resizeEvent(self, event):")
if start != -1:
    end = text.find("    def load_files(self):", start)
    if end != -1:
        text = text[:start] + text[end:]

# Remove accidental minimum/maximum width constraints introduced by earlier
# patches so the original proportions can be preserved inside the scroll area.
text = text.replace("        self.setMinimumSize(760, 600)\n", "")
text = text.replace("        self.list.setMinimumWidth(220)\n", "        self.list.setMinimumWidth(360)\n")
text = text.replace("        self.list.setMaximumWidth(list_width)\n", "")
text = text.replace("        self.list.setMinimumWidth(list_width)\n", "")
text = text.replace("        self.cover.setFixedSize(280, 280)\n", "        self.cover.setFixedSize(340, 340)\n")
text = text.replace("        self.body_layout = body\n", "")
text = text.replace("        self.controls_layout = controls\n", "")

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase now uses a stable scrollable layout at narrow window sizes.")
