from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOW = ROOT / "gui" / "mp3_showcase_page.py"


def main():
    text = SHOW.read_text(encoding="utf-8-sig")

    start = text.find("    def show_item(self, row):")
    if start < 0:
        raise SystemExit("show_item() not found")

    end = text.find("\n    def ", start + 10)
    if end < 0:
        end = len(text)

    block = text[start:end]

    if "persisted = self.load_persisted_mp3_info(str(path))" not in block:
        marker = '        album = str(album or "").strip()\n'
        if marker in block:
            block = block.replace(
                marker,
                marker + '\n        persisted = self.load_persisted_mp3_info(str(path))\n',
                1,
            )
        else:
            # Fallback: inject immediately after tuple unpacking.
            marker2 = ") = row\n\n"
            if marker2 not in block:
                raise SystemExit("Could not find show_item insertion point")
            block = block.replace(
                marker2,
                marker2 + '        persisted = self.load_persisted_mp3_info(str(path))\n\n',
                1,
            )

    text = text[:start] + block + text[end:]
    SHOW.write_text(text, encoding="utf-8-sig")
    print("OK: persisted metadata is now initialized inside show_item().")


if __name__ == "__main__":
    main()
