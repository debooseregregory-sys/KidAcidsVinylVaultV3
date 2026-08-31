import re
from pathlib import Path

# Bestanden die we willen fixen (pas aan indien nodig)
files = [
    "gui/cd_showcase_page.py",
    "gui/livesets_showcase_page.py",
    "gui/release_showcase_page.py",
    "gui/database_settings_panel.py",
    "gui/discogs_settings_panel.py",
    "gui/help_page.py",
    "gui/liveset_detail_page.py",
    "gui/mp3_duplicate_cleaner.py",
    "gui/mp3_showcase_page.py",
    "gui/release_board_page.py",
]

# Matcht paint_accent("...") of paint_accent("""...""") en pakt alleen de string eruit
pattern = re.compile(r'paint_accent\((""".*?"""|"(?:[^"\\]|\\.)*")\)', re.DOTALL)

for f in files:
    path = Path(f)
    if not path.exists():
        print(f"SKIP (niet gevonden): {f}")
        continue
    original = path.read_text(encoding="utf-8")
    fixed, n = pattern.subn(r"\1", original)
    if n > 0:
        path.write_text(fixed, encoding="utf-8")
        print(f"FIXED: {f} — {n} vervanging(en)")
    else:
        print(f"GEEN wijziging: {f}")