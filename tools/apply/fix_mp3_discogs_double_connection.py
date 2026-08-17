from pathlib import Path
import re

p = Path('gui/mp3_library_page.py')
text = p.read_text(encoding='utf-8-sig')

# Keep the FIRST persist_discogs_release(self, conn, path) and remove any duplicate
# definition that follows it before save().
pattern = re.compile(r'(    def persist_discogs_release\(self, conn, path\):.*?\n\n)(    def persist_discogs_release\(self, conn, path\):.*?\n\n)(    def save\(self\):)', re.S)
match = pattern.search(text)
if match:
    text = text[:match.start()] + match.group(1) + match.group(3) + text[match.end():]

# Never open a second connection from save() merely to ensure columns.
# Schema setup should happen during page/dialog startup, not during an active save transaction.
text = text.replace('            ensure_mp3_discogs_columns()\n            self.persist_discogs_release(conn, path)', '            self.persist_discogs_release(conn, path)')
text = text.replace('            self.persist_discogs_release(conn, path)\n            conn.commit()\n\n            self.accept()', '            self.persist_discogs_release(conn, path)\n            conn.commit()\n\n            self.accept()')

p.write_text(text, encoding='utf-8-sig')

# Report remaining duplicate definitions and in-save schema calls.
count = len(re.findall(r'^    def persist_discogs_release\(self, conn, path\):', text, re.M))
print('persist_discogs_release definitions:', count)
print('ensure call inside save:', '            ensure_mp3_discogs_columns()' in text)
print('OK')
