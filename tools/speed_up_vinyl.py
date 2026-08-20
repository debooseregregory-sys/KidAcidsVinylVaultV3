from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = "            self.angle = (self.angle + 2.6) % 360.0"
new = "            self.angle = (self.angle + 3.4) % 360.0"

if old not in s:
    print("FOUT: draaisnelheid 2.6 niet gevonden")
    raise SystemExit(1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("OK - vinyl draait nu sneller: 3.4")
