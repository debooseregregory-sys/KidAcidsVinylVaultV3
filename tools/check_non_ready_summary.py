from pathlib import Path
from collections import Counter
import csv

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / "reports" / "niet_klaar_releases.csv"


def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"Rapport niet gevonden: {CSV_PATH}")

    counter = Counter()
    total = 0

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            total += 1
            missing = (row.get("ONTBREKEND") or "").strip()
            if not missing:
                counter["GEEN OPMERKING"] += 1
                continue

            for item in missing.split(" | "):
                item = item.strip()
                if item.startswith("TRACK "):
                    if ": POSITIE" in item:
                        counter["TRACK POSITIE"] += 1
                    elif ": TITEL" in item:
                        counter["TRACK TITEL"] += 1
                    else:
                        counter["TRACK"] += 1
                elif item.startswith("MP3 ONTBREEKT BIJ"):
                    counter["MP3"] += 1
                elif item.startswith("DUBBELE POSITIES:"):
                    counter["DUBBELE POSITIES"] += 1
                else:
                    counter[item] += 1

    print("=" * 70)
    print("VINYLVAULT - SAMENVATTING NIET-KLAAR")
    print("=" * 70)
    print(f"Niet-klaar releases : {total}")
    print()
    for name, count in counter.most_common():
        print(f"{name:<28} {count:>6}")
    print("=" * 70)
    print("Database gewijzigd : NEE")


if __name__ == "__main__":
    main()
