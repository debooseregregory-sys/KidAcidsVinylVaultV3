from pathlib import Path
import re

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

start = s.find("        # CLEAN TECHNICAL DISPLAY STRIP.")
if start == -1:
    print("FOUT: CLEAN TECHNICAL DISPLAY STRIP niet gevonden")
    raise SystemExit(1)

end = s.find("        #", start + 10)
if end == -1:
    end = len(s)

new_block = '''        # CLEAN TECHNICAL DISPLAY STRIP.
        # Stops well before the pitch fader.
        strip = QRectF(120, h - 92, max(220.0, w - 300.0), 58)

        p.setPen(QPen(QColor("#2d2f36"), 1))
        p.setBrush(QBrush(QColor("#0d0e12")))
        p.drawRoundedRect(strip, 7, 7)

        self._text(
            p,
            QRectF(
                strip.x() + 12,
                strip.y() + 7,
                strip.width() - 24,
                20
            ),
            "33 RPM   |   DIRECT DRIVE   |   STABLE PLATTER",
            8,
            MUTED,
            QFont.Weight.Bold,
            Qt.AlignmentFlag.AlignCenter
        )

'''

s = s[:start] + new_block + s[end:]

p.write_text(s, encoding="utf-8")
print("OK - onderste displayblok volledig vervangen")
print("OK - vreemde tekens verwijderd")
print("OK - display stopt vóór de pitchfader")
