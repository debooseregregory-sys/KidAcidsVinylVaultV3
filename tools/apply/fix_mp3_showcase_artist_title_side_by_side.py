from pathlib import Path

path = Path('gui/mp3_showcase_page.py')
text = path.read_text(encoding='utf-8-sig')

old = '''            text = f"{artist}\\n{title}" if artist and title else (artist or title or name)\n            item = QListWidgetItem(text)\n'''
new = '''            if artist and title:\n                text = f"{artist}    —    {title}"\n            else:\n                text = artist or title or name\n            item = QListWidgetItem(text)\n'''

if old not in text:
    raise SystemExit('Artist/title layout block not found; no changes made.')

text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('OK: artiest en track staan nu naast elkaar.')
