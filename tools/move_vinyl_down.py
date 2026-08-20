from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = "        cy = 300 + max(0.0, h - 610.0) * 0.12"
new = "        cy = 450 + max(0.0, h - 610.0) * 0.12"

if old not in s:
    raise SystemExit("FOUT: huidige cy-regel niet gevonden")

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("OK - vinyl 150 px naar beneden")
