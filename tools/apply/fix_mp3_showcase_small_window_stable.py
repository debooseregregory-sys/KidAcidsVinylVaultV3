from pathlib import Path

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

# Keep the page from being squeezed into an unusable width.
needle = '    def __init__(self, parent=None):\n        super().__init__(parent)\n'
replacement = (
    '    def __init__(self, parent=None):\n'
    '        super().__init__(parent)\n'
    '        self.setMinimumSize(760, 600)\n'
)
if needle in text and 'self.setMinimumSize(760, 600)' not in text:
    text = text.replace(needle, replacement, 1)

# Reduce the hard minimum on the library list so the detail card keeps room.
text = text.replace(
    'self.list.setMinimumWidth(360)',
    'self.list.setMinimumWidth(220)',
)

# Do not force a large cover at narrow sizes; resizeEvent below will scale it.
text = text.replace(
    'self.cover.setFixedSize(340, 340)',
    'self.cover.setFixedSize(280, 280)',
)

# Store the detail card so resizeEvent can size the cover against its actual width.
text = text.replace(
    '        card = QFrame()\n',
    '        card = QFrame()\n        self.detail_card = card\n',
    1,
)

# Remove accidental malformed responsive assignments if previous patches inserted them.
text = text.replace('        self.body_layout = body\n', '')
text = text.replace('        self.controls_layout = controls\n', '')

# Add a single resize handler before load_files().
marker = '    def load_files(self):\n'
method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        width = max(760, self.width())\n\n        # Give the left list a stable but smaller share when the window shrinks.\n        list_width = max(220, min(360, int(width * 0.30)))\n        self.list.setMinimumWidth(list_width)\n        self.list.setMaximumWidth(list_width)\n\n        # Scale the cover so it never consumes the whole detail card.\n        card_width = max(300, self.detail_card.width())\n        cover_size = max(160, min(280, int((card_width - 70) / 2)))\n        self.cover.setFixedSize(cover_size, cover_size)\n\n''' 
if marker in text and 'def resizeEvent(self, event):' not in text:
    text = text.replace(marker, method + marker, 1)

p.write_text(text, encoding='utf-8-sig')
print('OK: MP3 Showcase small-window layout stabilized.')
