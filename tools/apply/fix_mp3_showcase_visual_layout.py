from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"

NEW_DECK = r'''class VinylDeckWidget(QWidget):
    """Compact, realistic turntable for the MP3 Showcase."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.power_on = True
        self.angle = 0.0
        self.arm_progress = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(32)
        self.timer.timeout.connect(self._tick)
        self.setMinimumHeight(390)
        self.setMaximumHeight(470)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_track(self, artist, title):
        self.artist = str(artist or "Onbekende artiest").strip() or "Onbekende artiest"
        self.title = str(title or "-").strip() or "-"
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing) and self.power_on
        if self.playing:
            self.timer.start()
        else:
            self.timer.start()
        self.update()

    def set_power(self, on):
        self.power_on = bool(on)
        if not self.power_on:
            self.playing = False
        self.update()

    def _tick(self):
        if self.playing:
            self.angle = (self.angle + 2.8) % 360.0
        target = 1.0 if self.playing else 0.0
        self.arm_progress += (target - self.arm_progress) * 0.10
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = float(self.width()), float(self.height())
        pink = QColor("#d84b91")
        p.fillRect(self.rect(), QColor("#0b0b0f"))

        deck = QRectF(8, 8, w - 16, h - 16)
        p.setBrush(QBrush(QColor("#1b1b21")))
        p.setPen(QPen(QColor("#46414b"), 1))
        p.drawRoundedRect(deck, 14, 14)
        p.setBrush(QBrush(QColor("#121217")))
        p.setPen(QPen(QColor("#2d2931"), 1))
        p.drawRoundedRect(QRectF(18, 18, w - 36, h - 36), 10, 10)

        p.setPen(pink)
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Black))
        p.drawText(QRectF(28, 26, 280, 20), Qt.AlignmentFlag.AlignLeft, "KID ACID'S VINYL VAULT")
        p.setPen(QColor("#77727d"))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.drawText(QRectF(28, 45, 250, 18), Qt.AlignmentFlag.AlignLeft, "VINYL DECK • 33⅓ RPM")

        # Platter stays deliberately compact so the complete showcase fits.
        r = min(w * 0.255, h * 0.315)
        cx = w * 0.405
        cy = 55 + r
        p.setPen(QPen(QColor("#5a5560"), 2))
        p.setBrush(QBrush(QColor("#2b2930")))
        p.drawEllipse(QPointF(cx, cy), r + 9, r + 9)
        p.setPen(QPen(QColor("#16151a"), 2))
        p.setBrush(QBrush(QColor("#050507")))
        p.drawEllipse(QPointF(cx, cy), r, r)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for f in (.95, .91, .87, .83, .79, .75, .71, .67, .63, .59):
            p.setPen(QPen(QColor("#18171c"), 1))
            p.drawEllipse(QPointF(0, 0), r*f, r*f)
        p.setPen(QPen(QColor(210, 210, 220, 35), 2))
        p.drawArc(QRectF(-r*.86, -r*.86, r*1.72, r*1.72), 18*16, 54*16)
        p.restore()

        lr = r * .27
        p.setBrush(QBrush(QColor("#8e315e")))
        p.setPen(QPen(QColor("#df78a4"), 1))
        p.drawEllipse(QPointF(cx, cy), lr, lr)
        p.setPen(QColor("#f2c4d8"))
        p.setFont(QFont("Segoe UI", max(7, int(lr*.20)), QFont.Weight.Bold))
        p.drawText(QRectF(cx-lr, cy-7, lr*2, 14), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setBrush(QBrush(QColor("#d5d2d7")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 4, 4)

        # Realistic straight tonearm: pivot -> tube -> headshell -> stylus.
        # The playing stylus is placed on the OUTER groove area, never near
        # the label.  The arm moves between a rest position and that point.
        pivot = QPointF(w * .785, 91)
        outer_target = QPointF(cx + r*.72, cy - r*.42)
        rest_target = QPointF(w * .72, 78)
        target = QPointF(
            rest_target.x() + (outer_target.x()-rest_target.x())*self.arm_progress,
            rest_target.y() + (outer_target.y()-rest_target.y())*self.arm_progress,
        )

        dx, dy = target.x()-pivot.x(), target.y()-pivot.y()
        length = max(1.0, (dx*dx + dy*dy) ** .5)
        ux, uy = dx/length, dy/length
        shell = QPointF(target.x()+ux*15, target.y()+uy*15)

        # Counterweight.
        counter = QPointF(pivot.x()+22, pivot.y()-2)
        p.setPen(QPen(QColor("#111115"), 13, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(counter, pivot)
        p.setPen(QPen(QColor("#77727c"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(counter, pivot)
        p.setBrush(QBrush(QColor("#3b3940")))
        p.setPen(QPen(QColor("#aaa5ad"), 1))
        p.drawEllipse(counter, 13, 13)

        # Arm tube.
        p.setPen(QPen(QColor("#0a0a0c"), 13, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, target)
        p.setPen(QPen(QColor("#b9b4bc"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, target)
        p.setPen(QPen(QColor("#ece9ed"), 1))
        p.drawLine(QPointF(pivot.x(), pivot.y()-2), QPointF(target.x(), target.y()-2))

        # Headshell and cartridge aligned with the arm.
        p.save()
        p.translate(shell)
        p.rotate(0 if abs(dx) < .001 else __import__('math').degrees(__import__('math').atan2(dy, dx)))
        p.setBrush(QBrush(QColor("#d0ccd2")))
        p.setPen(QPen(QColor("#5a5660"), 1))
        p.drawRoundedRect(QRectF(-2, -7, 28, 14), 3, 3)
        p.setBrush(QBrush(pink))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(15, -5, 11, 10), 2, 2)
        p.restore()

        # Stylus tip sits just outside the playable groove area.
        stylus = QPointF(shell.x()+ux*12, shell.y()+uy*12)
        p.setPen(QPen(QColor("#e6e3e8"), 2))
        p.drawLine(QPointF(stylus.x(), stylus.y()-1), QPointF(stylus.x()+ux*3, stylus.y()+uy*8))

        # Pivot cap and arm rest.
        p.setBrush(QBrush(QColor("#343139")))
        p.setPen(QPen(QColor("#aaa5ad"), 1))
        p.drawEllipse(pivot, 15, 15)
        p.setBrush(QBrush(QColor("#111115")))
        p.drawEllipse(pivot, 5, 5)
        rest = QPointF(w*.70, 94)
        p.setPen(QPen(QColor("#77727c"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(rest, QPointF(rest.x()+10, rest.y()-18))

        # Pitch control, kept clear of the artwork.
        pitch_x = w - 46
        top, bottom = 125, h - 122
        p.setPen(QPen(QColor("#5b5660"), 2))
        p.drawLine(QPointF(pitch_x, top), QPointF(pitch_x, bottom))
        for i in range(-4, 5):
            y = (top+bottom)/2 - i*18
            tick = 13 if i % 2 == 0 else 8
            p.drawLine(QPointF(pitch_x-tick, y), QPointF(pitch_x, y))
        p.setBrush(QBrush(QColor("#d0cbd2")))
        p.drawRoundedRect(QRectF(pitch_x-12, (top+bottom)/2-5, 24, 10), 3, 3)
        p.setPen(QColor("#8d8792"))
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        p.drawText(QRectF(pitch_x-18, bottom+6, 36, 15), Qt.AlignmentFlag.AlignCenter, "PITCH")
        p.drawText(QRectF(pitch_x-18, (top+bottom)/2-8, 36, 15), Qt.AlignmentFlag.AlignCenter, "0")
        p.drawText(QRectF(pitch_x-18, top-16, 36, 15), Qt.AlignmentFlag.AlignCenter, "+8")
        p.drawText(QRectF(pitch_x-18, bottom+22, 36, 15), Qt.AlignmentFlag.AlignCenter, "-8")

        # Compact footer that is always inside the widget.
        base = h - 86
        p.setPen(QColor("#77727d"))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.drawText(QRectF(28, base, w-80, 16), Qt.AlignmentFlag.AlignLeft, "33⅓ RPM   •   DIRECT DRIVE")
        p.setPen(pink if self.power_on else QColor("#55515a"))
        p.drawText(QRectF(28, base+18, 150, 16), Qt.AlignmentFlag.AlignLeft, "● POWER ON" if self.power_on else "● POWER OFF")
        p.setPen(QColor("#f2f0f3"))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(QRectF(185, base, w-245, 18), Qt.AlignmentFlag.AlignLeft, self.artist)
        p.setFont(QFont("Segoe UI", 12, QFont.Weight.Black))
        p.drawText(QRectF(185, base+19, w-245, 20), Qt.AlignmentFlag.AlignLeft, self.title)
        p.end()
'''


def main():
    if not TARGET.exists():
        raise SystemExit(f"Bestand niet gevonden: {TARGET}")

    master = subprocess.check_output(
        ["git", "show", "origin/master:gui/mp3_showcase_page.py"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )

    # Restore the proven Showcase page structure from master, then replace only
    # the visual deck. This brings back cover, metadata and track list without
    # touching the database or other pages.
    content = re.sub(
        r"class VinylDeckWidget\(QWidget\):.*?\n\nclass MP3ShowcasePage\(QWidget\):",
        NEW_DECK + "\n\n\nclass MP3ShowcasePage(QWidget):",
        master,
        count=1,
        flags=re.S,
    )
    if content == master:
        raise SystemExit("VinylDeckWidget kon niet veilig worden vervangen.")

    # Make the left MP3 list easier to read: artist and title on separate lines.
    content = content.replace(
        'text = f"{artist} — {title}".strip(" —") if artist or title else name',
        'text = f"{artist}\\n{title}" if artist and title else (artist or title or name)',
    )
    content = content.replace(
        'QListWidget::item{padding:8px;',
        'QListWidget::item{padding:10px; min-height:42px;',
    )

    TARGET.write_text(content, encoding="utf-8", newline="\n")
    print("MP3 Showcase visual layout hersteld en deck verbeterd.")
    print(TARGET)


if __name__ == "__main__":
    main()
