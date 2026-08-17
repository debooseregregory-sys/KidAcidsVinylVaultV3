from pathlib import Path

path = Path('gui/mp3_showcase_page.py')
text = path.read_text(encoding='utf-8-sig')

# Keep references to the two layouts so resizeEvent can switch their direction.
old = '''        body = QHBoxLayout()\n        body.setSpacing(20)\n'''
new = '''        body = QHBoxLayout()\n        body.setSpacing(20)\n        self.body_layout = body\n'''
if old not in text:
    raise SystemExit('body layout marker not found')
text = text.replace(old, new, 1)

old = '''        top = QHBoxLayout()\n        top.setSpacing(22)\n'''
new = '''        top = QHBoxLayout()\n        top.setSpacing(22)\n        self.top_layout = top\n'''
if old not in text:
    raise SystemExit('top layout marker not found')
text = text.replace(old, new, 1)

# Replace the fixed 340x340 cover with a responsive square.
old = '''        self.cover = QLabel("NO COVER")\n        self.cover.setFixedSize(340, 340)\n'''
new = '''        self.cover = QLabel("NO COVER")\n        self.cover.setMinimumSize(180, 180)\n        self.cover.setMaximumSize(340, 340)\n        self.cover.setSizePolicy(\n            self.cover.sizePolicy().horizontalPolicy(),\n            self.cover.sizePolicy().verticalPolicy(),\n        )\n'''
if old not in text:
    raise SystemExit('cover size marker not found')
text = text.replace(old, new, 1)

# Add a resize handler immediately before load_files.
marker = '''    def load_files(self):\n'''
method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        # Desktop: list and showcase card side by side.\n        # Narrow window: stack them vertically so the cover/buttons never\n        # get squeezed into the information column.\n        narrow = self.width() < 1050\n\n        self.body_layout.setDirection(\n            QVBoxLayout.Direction.TopToBottom\n            if narrow\n            else QVBoxLayout.Direction.LeftToRight\n        )\n\n        self.top_layout.setDirection(\n            QVBoxLayout.Direction.TopToBottom\n            if self.width() < 780\n            else QVBoxLayout.Direction.LeftToRight\n        )\n\n        if self.width() < 600:\n            cover_size = min(240, max(180, self.width() - 80))\n        elif self.width() < 900:\n            cover_size = 260\n        else:\n            cover_size = 340\n\n        self.cover.setFixedSize(cover_size, cover_size)\n\n\n'''
if marker not in text:
    raise SystemExit('load_files marker not found')
text = text.replace(marker, method + marker, 1)

# Keep the showcase card from becoming absurdly narrow on desktop.
text = text.replace(
    '        self.list.setMinimumWidth(360)\n',
    '        self.list.setMinimumWidth(280)\n',
    1,
)

path.write_text(text, encoding='utf-8-sig')
print('OK: MP3 Showcase responsive layout installed.')
