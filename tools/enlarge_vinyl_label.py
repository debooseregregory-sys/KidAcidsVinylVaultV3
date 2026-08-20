from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = "        label_r = min(78.0, r * .34)"
new = "        label_r = min(105.0, r * .45)"

if old not in s:
    print("FOUT: huidige label-regel niet gevonden")
    raise SystemExit(1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("OK - middenlabel VEEL groter gemaakt")
