from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = "        pitch_x = 105"
new = "        pitch_x = w - 43"

count = s.count(old)

if count != 2:
    raise SystemExit(f"FOUT: pitch_x = 105 is {count} keer gevonden, verwacht 2")

s = s.replace(old, new)

p.write_text(s, encoding="utf-8")

print("OK - pitchfader terug naar rechts")
