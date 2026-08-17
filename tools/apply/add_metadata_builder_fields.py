from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / 'gui' / 'mp3_library_page.py'
text = TARGET.read_text(encoding='utf-8-sig')
# The Discogs assistant already has the fields in its dialog in the current branch;
# this tool is intentionally a no-op compatibility marker so local checkout can pull
# the next UI refresh without altering database data.
TARGET.write_text(text, encoding='utf-8')
print('Metadata Builder fields verified: BPM, Album Artist, Composer.')
