from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
text = p.read_text(encoding='utf-8-sig')

marker = 'from database.database import get_connection\n'
insert = '''from database.database import get_connection\n\ntry:\n    from mutagen.mp3 import MP3\n    MUTAGEN_AVAILABLE = True\nexcept ImportError:\n    MP3 = None\n    MUTAGEN_AVAILABLE = False\n'''

if 'MUTAGEN_AVAILABLE' not in text:
    if marker not in text:
        raise SystemExit('Import marker not found')
    text = text.replace(marker, insert, 1)

# Make duration fallback safe even when Mutagen is unavailable.
old = '''def format_duration(value, path=None):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n\n    if MUTAGEN_AVAILABLE and path:\n        try:\n            seconds = float(MP3(str(path)).info.length)\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n        except Exception:\n            pass\n\n    return "--:--"\n'''

if old not in text:
    alt = '''def format_duration(value, path=None):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n\n    if MUTAGEN_AVAILABLE and MP3 is not None and path:\n        try:\n            seconds = float(MP3(str(path)).info.length)\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n        except Exception:\n            pass\n\n    return "--:--"\n'''
    if alt in text:
        old = alt
    elif 'def format_duration' not in text:
        raise SystemExit('format_duration function not found')
    else:
        # Replace existing simple formatter conservatively.
        start = text.index('def format_duration')
        end = text.index('\n\ndef ensure_ignore_table', start)
        text = text[:start] + alt + text[end:]
        p.write_text(text, encoding='utf-8-sig')
        print('OK: Mutagen duration support restored.')
        raise SystemExit(0)

new = alt
text = text.replace(old, new, 1)
p.write_text(text, encoding='utf-8-sig')
print('OK: MUTAGEN_AVAILABLE and safe MP3 duration fallback restored.')
