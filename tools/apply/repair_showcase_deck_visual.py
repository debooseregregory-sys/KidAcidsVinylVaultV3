from pathlib import Path

path = Path("gui/mp3_showcase_page.py")
text = path.read_text(encoding="utf-8-sig")
backup = path.with_name("mp3_showcase_page_BEFORE_DECK_CENTER_REPAIR.py")
if not backup.exists():
    backup.write_text(text, encoding="utf-8")

old_layout = '''    def _layout(self):
        w, h = float(self.width()), float(self.height())
        r = max(145.0, min((w - 250.0) * 0.46, (h - 150.0) * 0.45))
        cx = min(w * 0.46, w - r - 100)
        cy = 300 + max(0.0, h - 610.0) * 0.12
        return w, h, cx, cy, r
'''
new_layout = '''    def _layout(self):
        w, h = float(self.width()), float(self.height())
        # Center the platter in the real turntable area and reserve the right
        # side for the tonearm and pitch control.
        deck_left = 34.0
        deck_right = max(deck_left + 320.0, w - 125.0)
        available_w = deck_right - deck_left
        r = max(145.0, min((available_w - 18.0) * 0.47, (h - 170.0) * 0.45))
        cx = deck_left + available_w * 0.50
        cy = 300 + max(0.0, h - 610.0) * 0.12
        return w, h, cx, cy, r
'''
if old_layout not in text:
    raise SystemExit("Could not find _layout block")
text = text.replace(old_layout, new_layout, 1)

start = text.index("        # STRAIGHT TONEARM. No elbow, no kink, one physical line.")
end = text.index("        # REAL PITCH FADER:", start)
new_tonearm = '''        # TONEARM / REST CRADLE
        # Parked beside the platter in a visible cradle; it swings onto the
        # record only when playback starts.
        pivot = QPointF(w - 112, 118)
        rest_stylus = QPointF(w - 173, 188)
        play_stylus = QPointF(cx + r * 0.56, cy + r * 0.08)
        stylus = QPointF(
            rest_stylus.x() + (play_stylus.x() - rest_stylus.x()) * self.arm_progress,
            rest_stylus.y() + (play_stylus.y() - rest_stylus.y()) * self.arm_progress,
        )
        dx = stylus.x() - pivot.x()
        dy = stylus.y() - pivot.y()
        length = max(1.0, hypot(dx, dy))
        ux, uy = dx / length, dy / length
        arm_angle = degrees(atan2(dy, dx))

        # Counterweight, collinear with the arm.
        counter = QPointF(pivot.x() - ux * 64, pivot.y() - uy * 64)
        p.setPen(QPen(QColor("#08090b"), 4))
        p.setBrush(QBrush(QColor("#484a52")))
        p.drawEllipse(counter, 17, 17)
        p.setPen(QPen(QColor("#7b7e87"), 2))
        p.drawEllipse(counter, 11, 11)
        p.setPen(QPen(QColor("#30323a"), 2))
        p.drawLine(QPointF(counter.x() - ux * 9, counter.y() - uy * 9),
                   QPointF(counter.x() + ux * 9, counter.y() + uy * 9))

        # Pivot housing.
        p.setPen(QPen(QColor("#050507"), 4))
        p.setBrush(QBrush(QColor("#303239")))
        p.drawEllipse(pivot, 28, 28)
        p.setPen(QPen(QColor("#70737c"), 2))
        p.drawEllipse(pivot, 18, 18)
        p.setPen(QPen(QColor("#a8aab1"), 2))
        p.drawLine(QPointF(pivot.x() - 7, pivot.y()), QPointF(pivot.x() + 7, pivot.y()))
        p.drawLine(QPointF(pivot.x(), pivot.y() - 7), QPointF(pivot.x(), pivot.y() + 7))

        # Physical rest cradle beside the pivot.
        cradle = QPointF(w - 174, 198)
        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(QColor("#17181d")))
        p.drawRoundedRect(QRectF(cradle.x() - 18, cradle.y() - 9, 36, 18), 6, 6)
        p.setPen(QPen(QColor("#666a73"), 2))
        p.drawArc(QRectF(cradle.x() - 11, cradle.y() - 8, 22, 16), 0, 180 * 16)
        p.setPen(QPen(QColor("#a2a4ab"), 2))
        p.drawLine(QPointF(cradle.x() - 9, cradle.y() - 1), QPointF(cradle.x() + 9, cradle.y() - 1))

        # Longer, substantial tonearm with proper turntable proportions.
        arm_end = QPointF(stylus.x() - ux * 25, stylus.y() - uy * 25)
        p.setPen(QPen(QColor("#07080a"), 16, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, arm_end)
        p.setPen(QPen(QColor("#c7c9cf"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, arm_end)
        p.setPen(QPen(QColor("#686b74"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, arm_end)

        # Headshell + cartridge aligned with the arm.
        shell = QPointF(stylus.x() - ux * 34, stylus.y() - uy * 34)
        p.save()
        p.translate(shell)
        p.rotate(arm_angle)
        p.setPen(QPen(QColor("#08090b"), 3))
        p.setBrush(QBrush(QColor("#b3b6bd")))
        p.drawRoundedRect(QRectF(-35, -9, 40, 18), 3, 3)
        p.setPen(QPen(QColor("#5d6068"), 1))
        p.drawLine(QPointF(-28, -5), QPointF(-3, -5))
        p.drawLine(QPointF(-28, 5), QPointF(-3, 5))
        p.setPen(QPen(QColor("#07080a"), 2))
        p.setBrush(QBrush(QColor("#25272e")))
        p.drawRoundedRect(QRectF(2, -8, 22, 16), 2, 2)
        p.setBrush(QBrush(PINK))
        p.drawRoundedRect(QRectF(17, -6, 9, 12), 2, 2)
        p.restore()

        # Stylus / cantilever.
        stylus_base = QPointF(stylus.x() - ux * 10, stylus.y() - uy * 10)
        p.setPen(QPen(QColor("#07080a"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(stylus_base, stylus)
        p.setPen(QPen(QColor("#f3f4f5"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(stylus_base, stylus)
        p.setPen(QPen(QColor("#ffffff"), 3))
        p.drawPoint(stylus)

        # Cue lever beside the pivot.
        p.setPen(QPen(QColor("#565861"), 3))
        p.drawLine(QPointF(pivot.x() + 34, pivot.y() + 18), QPointF(pivot.x() + 43, pivot.y() - 10))
        p.setPen(QPen(QColor("#a0a2a9"), 2))
        p.drawLine(QPointF(pivot.x() + 39, pivot.y() - 12), QPointF(pivot.x() + 50, pivot.y() - 12))

'''
text = text[:start] + new_tonearm + text[end:]

# Keep the deck UI ASCII-only so Windows font/encoding fallbacks cannot show
# replacement glyphs or mojibake-like symbols.
text = text.replace("33⅓ RPM   •   DIRECT DRIVE   •   STABLE PLATTER", "33 1/3 RPM   /   DIRECT DRIVE   /   STABLE PLATTER")
text = text.replace("  •  ", "  /  ")
text = text.replace("⅓", "1/3")

path.write_text(text, encoding="utf-8")
print(f"Patched: {path}")
print(f"Backup: {backup}")
