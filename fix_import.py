from pathlib import Path

path = Path(r".\gui\release_detail_page.py")
text = path.read_text(encoding="utf-8")

bad = """from database.database import (
from gui.mp3_search_dialog import MP3SearchDialog
    get_release_details,
)
"""

good = """from database.database import (
    get_release_details,
)

from gui.mp3_search_dialog import MP3SearchDialog
"""

if bad not in text:
    print("FOUT: verkeerde import-blok niet exact gevonden.")
    raise SystemExit(1)

text = text.replace(bad, good, 1)

path.write_text(text, encoding="utf-8")

print("IMPORT HERSTELD")
