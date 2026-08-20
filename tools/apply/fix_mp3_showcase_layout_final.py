from pathlib import Path

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

# Normalize the layout references introduced by the previous responsive patch.
text = text.replace(
    '    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\n',
    '    QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit, QPushButton,\n',
)
text = text.replace(
    '    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\n',
    '    QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit, QPushButton,\n',
)

# Store the main layouts on self so resizeEvent can change them safely.
text = text.replace(
    '        body = QHBoxLayout()\n',
    '        self.body_layout = QHBoxLayout()\n',
    1,
)
text = text.replace('        body.setSpacing(20)\n', '        self.body_layout.setSpacing(20)\n', 1)
text = text.replace('        body.addWidget(self.list)\n', '        self.body_layout.addWidget(self.list)\n', 1)
text = text.replace('        body.addWidget(card, 1)\n', '        self.body_layout.addWidget(card, 1)\n', 1)
text = text.replace('        root.addLayout(body, 1)\n', '        root.addLayout(self.body_layout, 1)\n', 1)

text = text.replace(
    '        top = QHBoxLayout()\n',
    '        self.top_layout = QHBoxLayout()\n',
    1,
)
text = text.replace('        top.setSpacing(22)\n', '        self.top_layout.setSpacing(22)\n', 1)
text = text.replace(
    '        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n',
    '        self.top_layout.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n',
    1,
)
text = text.replace('        top.addLayout(info, 1)\n', '        self.top_layout.addLayout(info, 1)\n', 1)
text = text.replace('        cl.addLayout(top)\n', '        cl.addLayout(self.top_layout)\n', 1)

text = text.replace(
    '        controls = QHBoxLayout()\n',
    '        self.controls_layout = QHBoxLayout()\n',
    1,
)
text = text.replace('        controls.addWidget(self.previous)\n', '        self.controls_layout.addWidget(self.previous)\n', 1)
text = text.replace('        controls.addWidget(self.play, 1)\n', '        self.controls_layout.addWidget(self.play, 1)\n', 1)
text = text.replace('        controls.addWidget(self.next)\n', '        self.controls_layout.addWidget(self.next)\n', 1)
text = text.replace('        cl.addLayout(controls)\n', '        cl.addLayout(self.controls_layout)\n', 1)

# Repair any remaining stale references from the broken patch.
text = text.replace('self.controls_layout.addWidget', 'self.controls_layout.addWidget')

# Add a real runtime responsive resize implementation once.
if '    def resizeEvent(self, event):\n' not in text:
    marker = '    def load_files(self):\n'
    method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        narrow = self.width() < 1050\n\n        if hasattr(self, "body_layout"):\n            self.body_layout.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        if hasattr(self, "top_layout"):\n            self.top_layout.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        if hasattr(self, "controls_layout"):\n            self.controls_layout.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        if hasattr(self, "list"):\n            self.list.setMinimumWidth(0 if narrow else 360)\n\n        if hasattr(self, "cover"):\n            if narrow:\n                size = max(200, min(280, self.width() - 80))\n            else:\n                size = 340\n\n            self.cover.setFixedSize(size, size)\n\n            pixmap = self.cover.pixmap()\n            if pixmap is not None and not pixmap.isNull():\n                self.cover.setPixmap(\n                    pixmap.scaled(\n                        size,\n                        size,\n                        Qt.AspectRatioMode.KeepAspectRatio,\n                        Qt.TransformationMode.SmoothTransformation,\n                    )\n                )\n\n'''
    if marker not in text:
        raise SystemExit('load_files marker not found')
    text = text.replace(marker, method + marker, 1)

p.write_text(text, encoding='utf-8-sig')
print('OK: MP3 Showcase layout references repaired and runtime resize added.')
