from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PAGE = BASE / "gui" / "release_board_page.py"
TILE = BASE / "gui" / "release_board_tile.py"

page = PAGE.read_text(encoding="utf-8-sig")
old = """                    r.catalog,\n                    r.year,\n                    r.checked,\n                    r.cover,\n"""
new = """                    r.catalog,\n                    r.year,\n                    r.storage_code,\n                    r.checked,\n                    r.cover,\n"""
if page.count(old) != 1:
    raise RuntimeError(f"SELECT-blok verwacht 1 keer, gevonden {page.count(old)}")
page = page.replace(old, new, 1)
page = page.replace('"year": row[5],\\n            "checked": row[6], "cover": row[7], "preferred_mp3": row[8]', '"year": row[5], "storage_code": row[6],\\n            "checked": row[7], "cover": row[8], "preferred_mp3": row[9]', 1)
PAGE.write_text(page, encoding="utf-8")

tile = TILE.read_text(encoding="utf-8-sig")
old2 = """        if data.get(\"year\"):\n            info_bits.append(str(data[\"year\"]))\n\n        info = QLabel(\"  •  \".join(info_bits) if info_bits else \"\")\n"""
new2 = """        if data.get(\"year\"):\n            info_bits.append(str(data[\"year\"]))\n        if data.get(\"storage_code\"):\n            info_bits.append(f\"Kast: {data['storage_code']}\")\n\n        info = QLabel(\"  •  \".join(info_bits) if info_bits else \"\")\n"""
if tile.count(old2) != 1:
    raise RuntimeError(f"info-blok verwacht 1 keer, gevonden {tile.count(old2)}")
tile = tile.replace(old2, new2, 1)
TILE.write_text(tile, encoding="utf-8")

print("KASTCODE TOEGEVOEGD AAN RELEASE BOARD")
