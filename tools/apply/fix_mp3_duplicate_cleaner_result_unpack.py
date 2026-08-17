from pathlib import Path
import re

p = Path('gui/mp3_duplicate_cleaner.py')
text = p.read_text(encoding='utf-8-sig')

old = '''                mp3_id, path, artist, title, album, year, checked, linked = item
                flags = []
'''
new = '''                (
                    mp3_id,
                    path,
                    artist,
                    title,
                    album,
                    year,
                    checked,
                    linked,
                    filesize,
                    duration,
                    bitrate,
                ) = item
                flags = []
'''

if old not in text:
    raise SystemExit('on_finished unpack-blok niet gevonden')

text = text.replace(old, new, 1)

old2 = '''        self.summary.setText(
            f"{exact_count} exacte dubbele groepen • "
            f"{track_count} dubbele track-kandidaten • "
            f"{duplicate_files} overtollige bestanden"
        )
'''
new2 = '''        self.summary.setText(
            f"{exact_count} exacte dubbele groepen • "
            f"{track_count} dubbele track-kandidaten • "
            f"{duplicate_files} overtollige bestanden"
        )
'''

# Keep existing summary unchanged; the important fix is the unpacking above.

p.write_text(text, encoding='utf-8-sig')
print('OK: duplicate cleaner resultaat-unpack hersteld.')
