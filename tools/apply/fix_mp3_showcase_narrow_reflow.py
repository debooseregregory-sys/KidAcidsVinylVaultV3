from pathlib import Path

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

# Keep references to the layouts that must change direction at runtime.
if 'self.body_layout = body' not in text:
    marker = '        body.setSpacing(20)\n'
    if marker not in text:
        raise SystemExit('body layout marker not found')
    text = text.replace(marker, marker + '        self.body_layout = body\n', 1)

if 'self.top_layout = top' not in text:
    marker = '        top.setSpacing(22)\n'
    if marker not in text:
        raise SystemExit('top layout marker not found')
    text = text.replace(marker, marker + '        self.top_layout = top\n', 1)

if 'self.controls_layout = controls' not in text:
    marker = '        controls = QHBoxLayout()\n'
    if marker not in text:
        raise SystemExit('controls layout marker not found')
    text = text.replace(marker, marker + '        self.controls_layout = controls\n', 1)

# Make the cover size flexible rather than permanently fixed.
text = text.replace(
    '        self.cover.setFixedSize(280, 280)\n',
    '        self.cover.setMinimumSize(160, 160)\n        self.cover.setMaximumSize(320, 320)\n',
    1,
)

# Replace the resizeEvent with a real reflow handler.
start = text.find('    def resizeEvent(self, event):\n')
end = text.find('    def load_files(self):\n')
if start == -1 or end == -1 or end <= start:
    raise SystemExit('existing resizeEvent block not found')

method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        w = self.width()\n        narrow = w < 1050\n        very_narrow = w < 850\n\n        # Main content: side-by-side when wide, stacked when narrow.\n        if hasattr(self, "body_layout"):\n            self.body_layout.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        # Detail header: cover and metadata side-by-side when wide, stacked when narrow.\n        if hasattr(self, "top_layout"):\n            self.top_layout.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        # Controls stack vertically at the smallest size so buttons never overlap the cover.\n        if hasattr(self, "controls_layout"):\n            self.controls_layout.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if very_narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        # Keep the library list useful without forcing the detail pane off screen.\n        if narrow:\n            self.list.setMinimumWidth(0)\n            self.list.setMaximumWidth(16777215)\n            self.list.setMinimumHeight(150)\n            self.list.setMaximumHeight(280)\n        else:\n            self.list.setMinimumWidth(220)\n            self.list.setMaximumWidth(360)\n            self.list.setMinimumHeight(0)\n            self.list.setMaximumHeight(16777215)\n\n        # Cover size follows the available width.\n        card_width = max(220, self.detail_card.width() if hasattr(self, "detail_card") else w)\n        if narrow:\n            cover = max(160, min(280, int((card_width - 50) * 0.60)))\n        else:\n            cover = min(320, max(220, int(card_width * 0.42)))\n        self.cover.setFixedSize(cover, cover)\n\n'''

text = text[:start] + method + text[end:]

# QBoxLayout is needed for Direction; add it to imports.
if 'QBoxLayout,' not in text:
    text = text.replace(
        '    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\n',
        '    QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit, QPushButton,\n',
        1,
    )

p.write_text(text, encoding='utf-8-sig')
print('OK: MP3 Showcase now reflows vertically on narrow windows.')
