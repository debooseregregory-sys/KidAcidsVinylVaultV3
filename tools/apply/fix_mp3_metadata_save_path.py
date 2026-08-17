from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"
text = TARGET.read_text(encoding="utf-8-sig")
# Ensure MetadataDialog.save defines its own path from the dialog state.
text = text.replace(
    "    def save(self):\n        if not MUTAGEN_AVAILABLE:",
    "    def save(self):\n        path = str(self.row[0] or \"\")\n        if not MUTAGEN_AVAILABLE:",
    1,
)
# Remove any duplicate local path assignment later in save if present.
text = text.replace(
    "\n        path = str(self.row[0])\n        if not Path(path).exists():",
    "\n        if not Path(path).exists():",
    1,
)
TARGET.write_text(text, encoding="utf-8-sig")
print("MP3 metadata save path fix toegepast")
