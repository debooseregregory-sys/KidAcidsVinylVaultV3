from pathlib import Path
import re

TARGET = Path("gui/mp3_showcase_page.py")
text = TARGET.read_text(encoding="utf-8-sig")

# Keep the deck visually stable when the surrounding layout becomes taller.
text = text.replace(
    'self.setMinimumSize(620, 610)',
    'self.setMinimumSize(560, 560)'
)

old = '''        size = max(330.0, min(w - 150.0, h - 235.0))\n        r = size / 2.0\n        cx, cy = w * 0.43, 80 + r\n'''
new = '''        # The platter is the reference object for the whole turntable.\n        # Never let the deck height stretch the arm or pitch control.\n        available_w = max(300.0, w - 150.0)\n        available_h = max(300.0, h - 245.0)\n        size = min(available_w, available_h)\n        size = max(300.0, min(size, 520.0))\n        r = size / 2.0\n        cx = w * 0.43\n        cy = 86.0 + r\n'''
if old not in text:
    raise SystemExit("Platter geometry block not found")
text = text.replace(old, new, 1)

old = '''        pivot = QPointF(w * 0.80, 135)\n        p.setPen(QPen(QColor("#08080a"), 5))\n        p.setBrush(QBrush(QColor("#343139")))\n        p.drawEllipse(pivot, 28, 28)\n        p.setPen(QPen(QColor("#817a84"), 2))\n        p.drawEllipse(pivot, 16, 16)\n        a = radians(self.arm_angle)\n        reach = r * 1.02\n        elbow = QPointF(pivot.x() - cos(a) * reach * .43, pivot.y() + sin(a) * reach * .43)\n        end = QPointF(cx + r * (.88 if self.playing else .62), cy - r * (.18 if self.playing else .54))\n        bend = QPointF((elbow.x() + end.x()) / 2 - sin(a) * 22, (elbow.y() + end.y()) / 2 - cos(a) * 22)\n'''
new = '''        # Realistic tonearm: fixed pivot, shallow sweep, stylus always lands\n        # near the outer groove area rather than reaching the centre label.\n        pivot = QPointF(w * 0.80, cy - r * 0.78)\n        p.setPen(QPen(QColor("#08080a"), 5))\n        p.setBrush(QBrush(QColor("#343139")))\n        p.drawEllipse(pivot, 28, 28)\n        p.setPen(QPen(QColor("#817a84"), 2))\n        p.drawEllipse(pivot, 16, 16)\n        a = radians(self.arm_angle)\n        reach = r * 1.05\n        elbow = QPointF(pivot.x() - cos(a) * reach * .34, pivot.y() + sin(a) * reach * .34)\n        groove_radius = r * (.89 if self.playing else .91)\n        end = QPointF(cx + groove_radius * cos(radians(-18)), cy + groove_radius * sin(radians(-18)))\n        bend = QPointF((elbow.x() + end.x()) / 2 - sin(a) * 18, (elbow.y() + end.y()) / 2 - cos(a) * 18)\n'''
if old not in text:
    raise SystemExit("Tonearm geometry block not found")
text = text.replace(old, new, 1)

old = '''        pitch_x = w - 74\n        top = 225\n        bottom = h - 205\n'''
new = '''        # Pitch control lives in its own fixed-height strip beside the platter.\n        # It therefore cannot become distorted when the widget gets taller.\n        pitch_x = w - 62\n        top = cy - r * .48\n        bottom = cy + r * .48\n'''
if old not in text:
    raise SystemExit("Pitch geometry block not found")
text = text.replace(old, new, 1)

old = '''        p.drawText(QRectF(28, h - 116, 200, 20), Qt.AlignmentFlag.AlignLeft, "33⅓ RPM   •   DIRECT DRIVE")\n        p.setPen(pink if self.power_on else QColor("#55515a"))\n        p.drawText(QRectF(28, h - 88, 180, 20), Qt.AlignmentFlag.AlignLeft, "● POWER ON" if self.power_on else "● POWER OFF")\n        p.setPen(QColor("#ffffff"))\n        p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))\n        p.drawText(QRectF(28, h - 60, w - 56, 24), Qt.AlignmentFlag.AlignLeft, self.artist)\n        p.setFont(QFont("Segoe UI", 18, QFont.Weight.Black))\n        p.drawText(QRectF(28, h - 37, w - 56, 25), Qt.AlignmentFlag.AlignLeft, self.title)\n'''
new = '''        footer_y = max(cy + r + 24, h - 118)\n        p.drawText(QRectF(28, footer_y, 240, 20), Qt.AlignmentFlag.AlignLeft, "33⅓ RPM   •   DIRECT DRIVE")\n        p.setPen(pink if self.power_on else QColor("#55515a"))\n        p.drawText(QRectF(28, footer_y + 24, 180, 20), Qt.AlignmentFlag.AlignLeft, "● POWER ON" if self.power_on else "● POWER OFF")\n        p.setPen(QColor("#ffffff"))\n        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))\n        p.drawText(QRectF(28, footer_y + 48, w - 56, 20), Qt.AlignmentFlag.AlignLeft, self.artist)\n        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Black))\n        p.drawText(QRectF(28, footer_y + 69, w - 56, 22), Qt.AlignmentFlag.AlignLeft, self.title)\n'''
if old not in text:
    raise SystemExit("Footer block not found")
text = text.replace(old, new, 1)

TARGET.write_text(text, encoding="utf-8")
print("Vinyl deck proportions fixed.")
