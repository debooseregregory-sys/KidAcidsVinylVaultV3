from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
text = p.read_text(encoding='utf-8-sig')

# Add mutagen fallback import.
if 'from mutagen.mp3 import MP3' not in text:
    marker = 'from database.database import get_connection\n'
    insert = '''from database.database import get_connection\n\ntry:\n    from mutagen.mp3 import MP3\nexcept ImportError:\n    MP3 = None\n'''
    if marker not in text:
        raise SystemExit('Import marker not found')
    text = text.replace(marker, insert, 1)

old = '''def format_duration(value):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n    return "--:--"\n'''

new = '''def format_duration(value, path=None):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n\n    if MP3 is not None and path:\n        try:\n            seconds = float(MP3(str(path)).info.length)\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n        except Exception:\n            pass\n\n    return "--:--"\n'''

if old in text:
    text = text.replace(old, new, 1)
else:
    if 'def format_duration(value, path=None):' not in text:
        raise SystemExit('format_duration function not found')

text = text.replace(
    'duration_text = format_duration(member["duration"])',
    'duration_text = format_duration(member["duration"], member["path"])',
)

p.write_text(text, encoding='utf-8-sig')
print('OK: duplicate cleaner now falls back to reading MP3 duration directly.')
