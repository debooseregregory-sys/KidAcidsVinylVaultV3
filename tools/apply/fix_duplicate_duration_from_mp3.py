from pathlib import Path

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

# Add Mutagen import if missing.
if "from mutagen.mp3 import MP3" not in text:
    marker = "from database.database import get_connection\n"
    insert = marker + "\ntry:\n    from mutagen.mp3 import MP3\n    MUTAGEN_AVAILABLE = True\nexcept Exception:\n    MP3 = None\n    MUTAGEN_AVAILABLE = False\n"
    if marker not in text:
        raise SystemExit("database import not found")
    text = text.replace(marker, insert, 1)

# Replace format_duration with DB-first / MP3-fallback implementation.
start = text.find("def format_duration(")
if start == -1:
    raise SystemExit("format_duration() not found")
end = text.find("\n\n", start)
if end == -1:
    raise SystemExit("end of format_duration() not found")

new_func = '''def format_duration(value, path=""):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n\n    if MUTAGEN_AVAILABLE and path:\n        try:\n            mp3_path = Path(str(path))\n            if mp3_path.is_file():\n                seconds = int(round(float(MP3(str(mp3_path)).info.length)))\n                return f"{seconds // 60}:{seconds % 60:02d}"\n        except Exception:\n            pass\n\n    return "--:--"'''

text = text[:start] + new_func + text[end:]

# Make existing calls pass the path too.
text = text.replace(
    'format_duration(member["duration"])',
    'format_duration(member["duration"], member["path"])'
)
text = text.replace(
    'format_duration(member["duration"], member.get("path"))',
    'format_duration(member["duration"], member.get("path"))'
)

p.write_text(text, encoding="utf-8-sig")
print("OK: duplicate cleaner reads MP3 duration when DB duration is empty.")
