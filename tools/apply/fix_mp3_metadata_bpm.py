from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

if "TBPM" not in text:
    text = text.replace(
        "from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TRCK, TPOS, TCOM, TPE2, COMM",
        "from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TRCK, TPOS, TCOM, TPE2, COMM, TBPM",
        1,
    )

anchor = '''            tags.delall("TDRC")\n            if text(self.year.text()):\n                tags.add(TDRC(encoding=3, text=text(self.year.text())))\n'''
replacement = '''            tags.delall("TDRC")\n            if text(self.year.text()):\n                tags.add(TDRC(encoding=3, text=text(self.year.text())))\n            tags.delall("TBPM")\n            if text(self.bpm.text()):\n                tags.add(TBPM(encoding=3, text=text(self.bpm.text())))\n'''
if anchor in text and 'tags.delall("TBPM")' not in text:
    text = text.replace(anchor, replacement, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 METADATA BUILDER: BPM WORDT OOK IN ID3 OPGESLAGEN")
