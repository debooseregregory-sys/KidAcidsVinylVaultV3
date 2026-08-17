from pathlib import Path
import re

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

# The real visible layout is self.body. Older patches accidentally changed
# self.body_layout, which is an unused layout and therefore had no effect.
text = text.replace(
    '        self.body_layout = QHBoxLayout()\n        body = QHBoxLayout()\n        body.setSpacing(20)\n',
    '        body = QHBoxLayout()\n        body.setSpacing(20)\n',
    1,
)
text = text.replace(
    '        self.body = QBoxLayout(QBoxLayout.Direction.LeftToRight)\n        self.body.setSpacing(20)\n',
    '        self.body = QBoxLayout(QBoxLayout.Direction.LeftToRight)\n        self.body.setSpacing(20)\n',
    1,
)

old = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        if not hasattr(self, "body_layout"):\n            return\n\n        compact = self.width() < 1100\n        direction = (\n            self.body_layout.Direction.TopToBottom\n            if compact\n            else self.body_layout.Direction.LeftToRight\n        )\n        self.body_layout.setDirection(direction)\n\n        available = max(180, min(340, int(self.width() * (0.32 if not compact else 0.55))))\n        self.cover.setFixedSize(available, available)\n'''

new = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        # IMPORTANT: self.body is the actual layout installed on root.\n        # Changing the unused self.body_layout had no visual effect.\n        compact = self.width() < 1100\n\n        if compact:\n            self.body.setDirection(QBoxLayout.Direction.TopToBottom)\n        else:\n            self.body.setDirection(QBoxLayout.Direction.LeftToRight)\n\n        # In compact mode, stack the cover/info inside the card as well.\n        if hasattr(self, "top"):\n            self.top.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if compact\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        # Keep the cover from forcing the card wider than the window.\n        card_width = max(280, self.detail_card.width())\n        if compact:\n            available = max(160, min(260, card_width - 44))\n        else:\n            available = max(180, min(340, int(card_width * 0.42)))\n        self.cover.setFixedSize(available, available)\n\n        # Keep the list usable without imposing a large fixed width.\n        if compact:\n            self.list.setMaximumWidth(16777215)\n        else:\n            self.list.setMaximumWidth(420)\n'''

if old not in text:
    raise SystemExit('resizeEvent block not found in current mp3_showcase_page.py')

text = text.replace(old, new, 1)

# Remove the stale dummy attributes if still present.
text = text.replace('        self.body_layout = QHBoxLayout()\n', '', 1)

p.write_text(text, encoding='utf-8-sig')
print('OK: MP3 Showcase resizeEvent now changes the real visible layouts.')
