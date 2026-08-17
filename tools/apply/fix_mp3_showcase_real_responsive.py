from pathlib import Path

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

# Import QBoxLayout for real runtime direction switching.
old_import = "    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\n"
new_import = "    QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit, QPushButton,\n"
if old_import in text and "QBoxLayout" not in text.split("from database.database", 1)[0]:
    text = text.replace(old_import, new_import, 1)

# Keep references to layouts used by resizeEvent.
text = text.replace(
    "        body = QHBoxLayout()\n        body.setSpacing(20)\n",
    "        self.body_layout = QHBoxLayout()\n        self.body_layout.setSpacing(20)\n",
    1,
)
text = text.replace("        body.addWidget(self.list)\n", "        self.body_layout.addWidget(self.list)\n", 1)
text = text.replace(
    "        top = QHBoxLayout()\n        top.setSpacing(22)\n",
    "        self.top_layout = QHBoxLayout()\n        self.top_layout.setSpacing(22)\n",
    1,
)
text = text.replace("        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n", "        self.top_layout.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n", 1)
text = text.replace("        top.addLayout(info, 1)\n        cl.addLayout(top)\n", "        self.top_layout.addLayout(info, 1)\n        cl.addLayout(self.top_layout)\n", 1)
text = text.replace(
    "        controls = QHBoxLayout()\n        self.previous = QPushButton(\"◀ VORIGE\")\n",
    "        self.controls_layout = QHBoxLayout()\n        self.previous = QPushButton(\"< VORIGE\")\n",
    1,
)
text = text.replace("        self.play = QPushButton(\"▶ PLAY\")\n", "        self.play = QPushButton(\"> PLAY\")\n", 1)
text = text.replace("        self.next = QPushButton(\"VOLGENDE ▶\")\n", "        self.next = QPushButton(\"VOLGENDE >\")\n", 1)
text = text.replace("        controls.addWidget(self.previous)\n", "        self.controls_layout.addWidget(self.previous)\n", 1)
text = text.replace("        controls.addWidget(self.play, 1)\n", "        self.controls_layout.addWidget(self.play, 1)\n", 1)
text = text.replace("        controls.addWidget(self.next)\n        cl.addLayout(controls)\n", "        self.controls_layout.addWidget(self.next)\n        cl.addLayout(self.controls_layout)\n", 1)
text = text.replace("        body.addWidget(card, 1)\n        root.addLayout(body, 1)\n", "        self.body_layout.addWidget(card, 1)\n        root.addLayout(self.body_layout, 1)\n", 1)

# Remove fixed cover size so it can shrink in narrow mode.
text = text.replace(
    "        self.cover.setFixedSize(340, 340)\n",
    "        self.cover.setMinimumSize(160, 160)\n        self.cover.setMaximumSize(340, 340)\n        self._cover_size = 340\n",
    1,
)

# Insert a real resize handler before load_files.
marker = "    def load_files(self):\n"
resize_method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        narrow = self.width() < 950\n        very_narrow = self.width() < 700\n\n        if narrow:\n            self.body_layout.setDirection(QBoxLayout.Direction.TopToBottom)\n            self.top_layout.setDirection(QBoxLayout.Direction.TopToBottom)\n            self.controls_layout.setDirection(QBoxLayout.Direction.TopToBottom)\n            self.list.setMinimumWidth(0)\n\n            available = max(160, min(280, self.width() - 70))\n            self._cover_size = available\n        else:\n            self.body_layout.setDirection(QBoxLayout.Direction.LeftToRight)\n            self.top_layout.setDirection(QBoxLayout.Direction.LeftToRight)\n            self.controls_layout.setDirection(QBoxLayout.Direction.LeftToRight)\n            self.list.setMinimumWidth(300)\n            self._cover_size = 340\n\n        self.cover.setFixedSize(\n            self._cover_size,\n            self._cover_size,\n        )\n\n        button_height = 42 if very_narrow else 38\n        for button in (self.previous, self.play, self.next):\n            button.setMinimumHeight(button_height)\n\n'''
if marker not in text:
    raise SystemExit("load_files marker not found")
if "def resizeEvent(self, event):" not in text:
    text = text.replace(marker, resize_method + marker, 1)

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase now switches layout direction at narrow window widths.")
