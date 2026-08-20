from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = '''        self._text(p, QRectF(cx - label_r, cy - 9, label_r * 2, 18), "KID ACID", 8, QColor("#f7e6ee"), QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(cx - label_r, cy + 8, label_r * 2, 14), "VINYL VAULT", 5, QColor("#e9a8c6"), QFont.Weight.Bold, Qt.AlignmentFlag.AlignCenter)
'''

new = '''        # LABEL TEXT - larger and spread across the label
        self._text(
            p,
            QRectF(cx - label_r * 0.82, cy - label_r * 0.48, label_r * 1.64, 28),
            "KID ACID",
            14,
            QColor("#f7e6ee"),
            QFont.Weight.Black,
            Qt.AlignmentFlag.AlignCenter
        )
        self._text(
            p,
            QRectF(cx - label_r * 0.82, cy + label_r * 0.30, label_r * 1.64, 22),
            "VINYL VAULT",
            10,
            QColor("#e9a8c6"),
            QFont.Weight.Bold,
            Qt.AlignmentFlag.AlignCenter
        )
'''

if old not in s:
    print("FOUT: oude labeltekst niet gevonden")
    raise SystemExit(1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("OK - labeltekst groter en verspreid geplaatst")
