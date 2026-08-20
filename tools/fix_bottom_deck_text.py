from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = '''        strip = QRectF(120, h - 92, max(250.0, w - 205), 58)
        p.setPen(QPen(QColor("#2d2f36"), 1))
        p.setBrush(QBrush(QColor("#0d0e12")))
        p.drawRoundedRect(strip, 7, 7)
        self._text(p, QRectF(strip.x() + 12, strip.y() + 7, strip.width() - 24, 17), "33 RPM   Ôàô   DIRECT DRIVE   ÔÇó   STABLE PLATTER", 8)
'''

new = '''        # BOTTOM TECHNICAL DISPLAY - kept clear of the pitch fader.
        strip = QRectF(120, h - 92, max(220.0, w - 285), 58)

        p.setPen(QPen(QColor("#2d2f36"), 1))
        p.setBrush(QBrush(QColor("#0d0e12")))
        p.drawRoundedRect(strip, 7, 7)

        self._text(
            p,
            QRectF(strip.x() + 12, strip.y() + 7, strip.width() - 24, 17),
            "33 RPM   |   DIRECT DRIVE   |   STABLE PLATTER",
            8,
            MUTED,
            QFont.Weight.Bold,
            Qt.AlignmentFlag.AlignCenter
        )
'''

if old not in s:
    print("FOUT: onderste tekststrip niet gevonden")
    raise SystemExit(1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("OK - vreemde tekens verwijderd en tekststrip vóór pitch gestopt")
