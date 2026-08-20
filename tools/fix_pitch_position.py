from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = "pitch_x = w - 43"
new = "pitch_x = w - 75"

if s.count(old) != 2:
    raise SystemExit(f"FOUT: {s.count(old)} regels gevonden, verwacht 2")

s = s.replace(old, new)

p.write_text(s, encoding="utf-8")

print("OK - pitch exact iets naar binnen geplaatst")
