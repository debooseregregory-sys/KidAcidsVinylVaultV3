from pathlib import Path

path = Path(__file__).resolve().parents[2] / "gui" / "mp3_showcase_page.py"
text = path.read_text(encoding="utf-8-sig")

old = '''        # Tonearm: pivot -> straight arm -> headshell.  No artificial elbow bend.\n        pivot = QPointF(w * .79, h * .235)\n        rest_head = QPointF(w * .70, h * .36)\n        groove_head = QPointF(cx + r * .76, cy - r * .10)\n        hp = QPointF(\n            rest_head.x() + (groove_head.x() - rest_head.x()) * self.arm_progress,\n            rest_head.y() + (groove_head.y() - rest_head.y()) * self.arm_progress,\n        )\n        arm_vec = hp - pivot\n        elbow = QPointF(pivot.x() + arm_vec.x() * .58, pivot.y() + arm_vec.y() * .58)\n\n        p.setPen(QPen(QColor("#0a0a0c"), 8))\n        p.drawLine(pivot, elbow)\n        p.setPen(QPen(QColor("#bcb7bf"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))\n        p.drawLine(pivot, elbow)\n        p.drawLine(elbow, hp)\n        p.setPen(QPen(QColor("#6d6871"), 2))\n        p.drawLine(pivot, elbow)\n'''

new = '''        # Tonearm: one continuous straight arm from the pivot to the headshell.\n        # The stylus moves only toward the outer playing groove; it never bends\n        # through an artificial elbow and never approaches the centre label.\n        pivot = QPointF(w * .79, h * .235)\n        rest_head = QPointF(w * .69, h * .36)\n        groove_head = QPointF(cx + r * .82, cy - r * .055)\n        hp = QPointF(\n            rest_head.x() + (groove_head.x() - rest_head.x()) * self.arm_progress,\n            rest_head.y() + (groove_head.y() - rest_head.y()) * self.arm_progress,\n        )\n\n        p.setPen(QPen(QColor("#09090b"), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))\n        p.drawLine(pivot, hp)\n        p.setPen(QPen(QColor("#c4bec6"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))\n        p.drawLine(pivot, hp)\n\n'''

if old not in text:
    raise SystemExit("Expected tonearm block not found; file was not changed.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Tonearm fixed: straight pivot-to-headshell arm, outer-groove position.")
