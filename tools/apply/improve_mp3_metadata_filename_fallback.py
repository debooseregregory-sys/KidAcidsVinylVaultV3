from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

# Add imports for filename parsing.
old = "from pathlib import Path\n"
new = "from pathlib import Path\nimport re\n"
if old in text and "import re\n" not in text:
    text = text.replace(old, new, 1)

# Replace read_real_tags with a version that reads actual tags first and only
# fills missing fields from filename/folder as a suggestion. It never writes
# anything automatically.
start = text.index("    @classmethod\n    def read_real_tags")
end = text.index("\n    def save(self):", start)

new_block = r'''    @staticmethod
    def _filename_suggestion(path, existing):
        """Build safe Tag & Rename-style suggestions without writing tags."""
        result = dict(existing)
        p = Path(path)
        stem = p.stem.strip()

        # Common pattern: "04 Artist - Title"
        match = re.match(r"^(?P<track>\d{1,3})\s+[-._ ]*\s*(?P<body>.+)$", stem)
        if match:
            if not result["track"]:
                result["track"] = match.group("track")
            stem = match.group("body").strip()

        # Artist - Title
        if " - " in stem:
            artist, title = stem.split(" - ", 1)
            artist = artist.strip()
            title = title.strip()
            if not result["artist"] and artist:
                result["artist"] = artist
            if not result["title"] and title:
                result["title"] = title
        elif not result["title"] and stem:
            result["title"] = stem

        # When there is no album tag, the immediate parent folder is the
        # safest album/release suggestion. The user still decides whether
        # to save it.
        if not result["album"]:
            parent = p.parent.name.strip()
            if parent and parent not in {"21. Discogs Database", "22. Started in 2025", "23. Discogs Database"}:
                result["album"] = parent

        return result

    @classmethod
    def read_real_tags(cls, path):
        result = {
            "artist": "", "title": "", "album": "", "year": "",
            "bpm": "", "track": "", "disc": "", "album_artist": "",
            "composer": "", "genre": "", "comment": "",
        }

        if MUTAGEN_AVAILABLE and Path(path).exists():
            try:
                try:
                    tags = ID3(path)
                except ID3NoHeaderError:
                    tags = None

                if tags is not None:
                    result["artist"] = cls._frame_text(tags, "TPE1")
                    result["title"] = cls._frame_text(tags, "TIT2")
                    result["album"] = cls._frame_text(tags, "TALB")
                    result["year"] = cls._frame_text(tags, "TDRC")
                    result["bpm"] = cls._frame_text(tags, "TBPM")
                    result["track"] = cls._frame_text(tags, "TRCK")
                    result["disc"] = cls._frame_text(tags, "TPOS")
                    result["album_artist"] = cls._frame_text(tags, "TPE2")
                    result["composer"] = cls._frame_text(tags, "TCOM")
                    result["genre"] = cls._frame_text(tags, "TCON")

                    comments = tags.getall("COMM")
                    if comments:
                        values = []
                        for frame in comments:
                            try:
                                values.extend(
                                    str(value).strip()
                                    for value in frame.text
                                    if str(value).strip()
                                )
                            except Exception:
                                pass
                        result["comment"] = " | ".join(dict.fromkeys(values))
            except Exception:
                pass

        # Important: only fill missing values. Existing tags always win.
        return cls._filename_suggestion(path, result)
'''

text = text[:start] + new_block + text[end:]

TARGET.write_text(text, encoding="utf-8")
print("Metadata Builder: echte tags eerst, daarna veilige bestandsnaam/map-suggesties voor lege velden.")
print("Voorbeeld: '04 DJ Urban - 69 cent.mp3' -> Track 04, Artist DJ Urban, Title 69 cent.")
print("Geen automatische database- of tagwijziging; alleen voorstellen in de editor.")
