import json
from pathlib import Path

root = Path(".")

namen = {
    "collection.json",
    "kid_acid_collection.json",
    "discogs_public_collection.json"
}

for p in root.rglob("*"):
    if p.is_file() and p.name in namen:
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)

            print("\n" + str(p))
            print("TYPE:", type(d).__name__)

            if isinstance(d, list):
                print("AANTAL:", len(d))
                if d and isinstance(d[0], dict):
                    print("KEYS:", list(d[0].keys())[:15])

            elif isinstance(d, dict):
                print("KEYS:", list(d.keys())[:15])
                for k, v in d.items():
                    if isinstance(v, list):
                        print("LIST:", k, "=", len(v))

        except Exception as e:
            print("\n" + str(p), "FOUT:", e)
