# ============================================================
# KID ACID'S VINYLVAULT V3
# SAFE CD EXCEL IMPORTER
# ============================================================

from pathlib import Path
import sys

import xlrd

from database.cd_database import ensure_cd_schema, import_cd_rows, count_cd_releases


DEFAULT_FILE = Path(r"C:\Users\andyb\Desktop\Cd Collectie.xls")


def read_xls(path):
    book = xlrd.open_workbook(str(path))
    sheet = book.sheet_by_index(0)
    rows = []
    for index in range(sheet.nrows):
        values = sheet.row_values(index)
        if len(values) < 2:
            continue
        artist = str(values[0] or "").strip()
        title = str(values[1] or "").strip()
        media_type = str(values[2] or "CD").strip() if len(values) >= 3 else "CD"
        if not artist or not title:
            continue
        rows.append({
            "artist": artist,
            "title": title,
            "media_type": media_type or "CD",
        })
    return rows


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    if not path.exists():
        print(f"BESTAND NIET GEVONDEN: {path}")
        return 1

    ensure_cd_schema()
    before = count_cd_releases()
    rows = read_xls(path)
    inserted, skipped = import_cd_rows(rows)
    after = count_cd_releases()

    print("=== CD IMPORT ===")
    print(f"Bestand       : {path}")
    print(f"Excel regels  : {len(rows)}")
    print(f"Reeds in DB   : {before}")
    print(f"Nieuw         : {inserted}")
    print(f"Overgeslagen  : {skipped}")
    print(f"Totaal CD DB  : {after}")
    print("Vinyl releases zijn niet aangepast.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
