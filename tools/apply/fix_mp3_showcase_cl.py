from pathlib import Path

path = Path('gui/mp3_showcase_page.py')
text = path.read_text(encoding='utf-8-sig')

if 'cl.addLayout(top)' not in text:
    raise SystemExit('Expected top layout insertion point not found.')

# The previous controls patch left the card layout object out while still
# calling cl.addLayout(...). Restore it exactly once immediately before the
# first use. Do not touch the rest of the showcase.
if 'cl = QVBoxLayout(card)' not in text:
    text = text.replace(
        '        cl.addLayout(top)\n',
        '        cl = QVBoxLayout(card)\n'
        '        cl.setContentsMargins(22, 22, 22, 22)\n'
        '        cl.setSpacing(12)\n'
        '        cl.addLayout(top)\n',
        1,
    )
else:
    # If a malformed duplicate exists, leave the existing definition alone.
    pass

path.write_text(text, encoding='utf-8-sig')
print('MP3 Showcase: card layout cl restored.')
