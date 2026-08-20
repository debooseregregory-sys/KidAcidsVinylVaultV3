from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = """        p.setPen(QPen(QColor(255, 255, 255, 24), 2))
        p.drawLine(QPointF(-r * .78, -r * .23), QPointF(r * .80, -r * .23))
"""

if old not in s:
    print("FOUT: witte vinyl-lijn niet gevonden")
    raise SystemExit(1)

s = s.replace(old, "", 1)
p.write_text(s, encoding="utf-8")

print("OK - witte vinyl-lijn verwijderd")
