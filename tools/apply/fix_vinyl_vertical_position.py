from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"

text = TARGET.read_text(encoding="utf-8-sig")
old = "        cy = 300 + max(0.0, h - 610.0) * 0.12\n"
new = "        # The platter must sit lower in the deck, visually centered in the main playing area.\n        cy = 350 + max(0.0, h - 610.0) * 0.08\n"

if old not in text:
    raise SystemExit("Expected platter layout line not found; file was not changed.")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")
print(f"Fixed vinyl vertical position in {TARGET}")
