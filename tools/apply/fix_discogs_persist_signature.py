from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "gui" / "mp3_library_page.py"


def main():
    text = LIB.read_text(encoding="utf-8-sig")

    old = "self.persist_discogs_release(conn, path)"
    new = "self.persist_discogs_release(path)"

    count = text.count(old)
    if count:
        text = text.replace(old, new)
        LIB.write_text(text, encoding="utf-8-sig")
        print(f"Hersteld: {count} verkeerde aanroep(en) aangepast.")
    else:
        print("Geen verkeerde persist_discogs_release(conn, path)-aanroep gevonden.")

    remaining = text.count(old)
    correct = text.count(new)
    print(f"Correcte aanroepen: {correct}")
    print(f"Verkeerde aanroepen: {remaining}")


if __name__ == "__main__":
    main()
