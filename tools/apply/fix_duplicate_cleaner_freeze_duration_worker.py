from pathlib import Path
import re

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

if "from mutagen.mp3 import MP3" not in text:
    marker = "from database.database import get_connection\n"
    insert = (
        "from database.database import get_connection\n\n"
        "try:\n"
        "    from mutagen.mp3 import MP3\n"
        "except ImportError:\n"
        "    MP3 = None\n"
    )
    if marker not in text:
        raise SystemExit("database import marker not found")
    text = text.replace(marker, insert, 1)

pattern = re.compile(
    r"def format_duration\(value(?:,\s*path)?\):\n"
    r"(?:    .*\n|\n)+?    return \"--:--\"\n",
    re.MULTILINE,
)
replacement = '''def format_duration(value):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n    return "--:--"\n'''
text, count = pattern.subn(replacement, text, count=1)
if count == 0 and "def format_duration(value):" not in text:
    raise SystemExit("format_duration function could not be located")

needle = "            groups.sort(\n"
worker_block = '''            # Read duration only for duplicate members, inside the worker thread.\n            if MP3 is not None:\n                duplicate_members = [\n                    member\n                    for group in groups\n                    for member in group["files"]\n                    if member.get("duration") in (None, "", 0)\n                ]\n                total_duration_reads = len(duplicate_members)\n                for duration_index, member in enumerate(duplicate_members, 1):\n                    if self._stop_requested or self.isInterruptionRequested():\n                        return\n                    try:\n                        member["duration"] = float(\n                            MP3(str(member["path"])).info.length\n                        )\n                    except Exception:\n                        member["duration"] = None\n                    if total_duration_reads and (\n                        duration_index == total_duration_reads\n                        or duration_index % 100 == 0\n                    ):\n                        self.progress.emit(\n                            duration_index,\n                            total_duration_reads,\n                        )\n\n'''
if needle not in text:
    raise SystemExit("groups.sort marker not found")
if "Read duration only for duplicate members" not in text:
    text = text.replace(needle, worker_block + needle, 1)

text = text.replace(
    'duration_text = format_duration(member["duration"], member["path"])',
    'duration_text = format_duration(member["duration"])',
)

text = text.replace(
    'if MUTAGEN_AVAILABLE and MP3 is not None and path:',
    'if False and MP3 is not None and path:',
)

p.write_text(text, encoding="utf-8-sig")
print("OK: duplicate duration reads moved out of GUI thread.")
