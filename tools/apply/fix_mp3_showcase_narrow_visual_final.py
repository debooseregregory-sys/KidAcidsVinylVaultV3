from pathlib import Path

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

# The cover and information were laid out horizontally. On a restored/smaller
# window that horizontal layout becomes too narrow and collides with the
# controls. Use a vertical detail layout so the Showcase remains stable at
# every window size.
old = "        top = QHBoxLayout()\n        top.setSpacing(22)\n"
new = "        top = QVBoxLayout()\n        top.setSpacing(14)\n"

if old not in text:
    raise SystemExit("Could not find MP3 Showcase detail top layout")

text = text.replace(old, new, 1)

# Give the cover a sensible responsive starting size instead of forcing the
# original 340x340 size. resizeEvent, when present, can still change it.
text = text.replace(
    "self.cover.setFixedSize(340, 340)",
    "self.cover.setMinimumSize(180, 180)\n        self.cover.setMaximumSize(340, 340)",
    1,
)

# Center the cover when it is in the vertical detail layout.
text = text.replace(
    '        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n',
    '        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignHCenter)\n',
    1,
)

# The info block is already a vertical layout and can remain below the cover.
# Remove any stale variables from previous responsive patches that can refer
# to deleted layouts.
text = text.replace('        self.body_layout = body\n', '')
text = text.replace('        self.controls_layout = controls\n', '')

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase narrow-window visual layout stabilized.")
