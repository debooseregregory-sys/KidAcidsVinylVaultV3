from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PAGE = BASE / "gui" / "release_board_page.py"
TILE = BASE / "gui" / "release_board_tile.py"

page = PAGE.read_text(encoding="utf-8-sig")
tile = TILE.read_text(encoding="utf-8-sig")

old_select = '''                    r.year,\n                    r.checked,\n                    r.cover,'''
new_select = '''                    r.year,\n                    r.storage_code,\n                    r.checked,\n                    r.cover,'''
if old_select not in page:
    raise RuntimeError("SELECT-blok voor storage_code niet gevonden")
page = page.replace(old_select, new_select, 1)

old_dict = '''            "label": row[3], "catalog": row[4], "year": row[5],\n            "checked": row[6], "cover": row[7], "preferred_mp3": row[8]'''
new_dict = '''            "label": row[3], "catalog": row[4], "year": row[5],\n            "storage_code": row[6], "checked": row[7],\n            "cover": row[8], "preferred_mp3": row[9]'''
if old_dict not in page:
    raise RuntimeError("Fallback-dict voor Board niet gevonden")
page = page.replace(old_dict, new_dict, 1)

old_dict_compact = '''        self.all_releases = [dict(row) if hasattr(row, "keys") else {'''
# no change needed for sqlite.Row case; kept for clarity.

old_tile_info = '''        if data.get("catalog"):\n            info_bits.append(str(data["catalog"]))\n        if data.get("year"):\n            info_bits.append(str(data["year"]))\n\n        info = QLabel("  •  ".join(info_bits) if info_bits else "")'''
new_tile_info = '''        if data.get("catalog"):\n            info_bits.append(str(data["catalog"]))\n        if data.get("year"):\n            info_bits.append(str(data["year"]))\n        if data.get("storage_code"):\n            info_bits.append(f"KAST: {data['storage_code']}")\n\n        info = QLabel("  •  ".join(info_bits) if info_bits else "")'''
if old_tile_info not in tile:
    raise RuntimeError("Info-blok van Board-kaart niet gevonden")
tile = tile.replace(old_tile_info, new_tile_info, 1)

PAGE.write_text(page, encoding="utf-8")
TILE.write_text(tile, encoding="utf-8")

print("BOARD KASTCODE CORRECT HERSTELD")
print("storage_code wordt nu uit releases geladen en op elke kaart getoond.")
