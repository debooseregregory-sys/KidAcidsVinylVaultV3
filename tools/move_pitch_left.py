from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old1 = "        pitch_x = w - 43"
new1 = "        pitch_x = 105"

count = s.count(old1)

if count != 2:
    raise SystemExit(f"FOUT: pitch_x-regel {count} keer gevonden, verwacht 2")

s = s.replace(old1, new1)

p.write_text(s, encoding="utf-8")

print("OK - pitchfader naar links op de deck verplaatst")
