from pathlib import Path

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

old = '''        # PHYSICAL POWER BUTTON.
        power = QPointF(70, h - 66)
        p.setPen(QPen(QColor("#050507"), 3))
        p.setBrush(QBrush(QColor("#292b32")))
        p.drawEllipse(power, 24, 24)
        p.setPen(QPen(QColor("#555862"), 1))
        p.drawEllipse(power, 19, 19)
        p.setPen(QPen(PINK if self.power_on else QColor("#555862"), 3))
        p.drawArc(QRectF(power.x() - 11, power.y() - 11, 22, 22), 45 * 16, 270 * 16)
        p.drawLine(QPointF(power.x(), power.y() - 14), QPointF(power.x(), power.y() + 1))
        self._text(p, QRectF(power.x() - 40, power.y() + 28, 80, 18), "POWER", 7, PINK if self.power_on else MUTED, QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
'''

new = '''        # SQUARE START / POWER BUTTON.
        power_x = 70.0
        power_y = h - 66.0
        power_rect = QRectF(power_x - 34, power_y - 24, 68, 48)

        p.setPen(QPen(QColor("#050507"), 3))
        p.setBrush(QBrush(QColor("#292b32")))
        p.drawRoundedRect(power_rect, 7, 7)

        p.setPen(QPen(QColor("#555862"), 1))
        p.setBrush(QBrush(QColor("#1d1f25")))
        p.drawRoundedRect(
            QRectF(power_x - 28, power_y - 18, 56, 36),
            5, 5
        )

        p.setPen(QPen(PINK if self.power_on else QColor("#555862"), 2))
        p.drawRoundedRect(
            QRectF(power_x - 22, power_y - 12, 44, 24),
            4, 4
        )

        self._text(
            p,
            QRectF(power_x - 22, power_y - 10, 44, 20),
            "START",
            8,
            PINK if self.power_on else MUTED,
            QFont.Weight.Black,
            Qt.AlignmentFlag.AlignCenter
        )
'''

if old not in s:
    print("FOUT: ronde POWER-knop niet gevonden")
    raise SystemExit(1)

s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

print("OK - ronde startknop vervangen door vierkante START-knop")
