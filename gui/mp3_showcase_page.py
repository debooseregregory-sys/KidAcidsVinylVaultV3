from pathlib import Path
import math

from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QPen,
    QBrush,
    QColor,
    QFont,
    QPainterPath,
    QLinearGradient,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QSizePolicy,
)

from database.database import get_connection

try:
    from mutagen.id3 import ID3, ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class VinylDeckWidget(QWidget):
    """Detailed visual turntable used by the MP3 Showcase.

    Playback itself remains handled by MP3ShowcasePage. This widget only
    animates the platter and the mechanical tonearm.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_progress = 0.0
        self.power_on = True
        self.pitch = 0.0

        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self.setMinimumHeight(500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_track(self, artist, title):
        self.artist = str(artist or "Onbekende artiest").strip() or "Onbekende artiest"
        self.title = str(title or "-").strip() or "-"
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing) and self.power_on
        self.update()

    def set_power(self, on):
        self.power_on = bool(on)
        if not self.power_on:
            self.playing = False
        self.update()

    def _tick(self):
        if self.playing and self.power_on:
            self.angle = (self.angle + 2.8) % 360.0

        target = 1.0 if self.playing and self.power_on else 0.0
        self.arm_progress += (target - self.arm_progress) * 0.075
        if abs(target - self.arm_progress) < 0.0005:
            self.arm_progress = target
        self.update()

    @staticmethod
    def _lerp(a, b, amount):
        return QPointF(
            a.x() + (b.x() - a.x()) * amount,
            a.y() + (b.y() - a.y()) * amount,
        )

    def _layout(self):
        w = float(self.width())
        h = float(self.height())
        # Keep the platter visually central and slightly lower, leaving room
        # for the mechanical controls above it.
        r = min((w - 235.0) * 0.44, (h - 185.0) * 0.44)
        r = max(145.0, min(r, 235.0))
        cx = min(w * 0.47, w - r - 105.0)
        cy = min(h * 0.53, h - r - 105.0)
        return w, h, cx, cy, r

    def _text(self, p, rect, text, size=9, color=None, weight=QFont.Weight.Bold,
              align=Qt.AlignmentFlag.AlignLeft):
        p.setPen(color or QColor("#8f919a"))
        p.setFont(QFont("Segoe UI", size, weight))
        p.drawText(rect, align, str(text))

    def _draw_shadowed_ellipse(self, p, center, rx, ry, shadow=QColor(0, 0, 0, 130)):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow))
        p.drawEllipse(QPointF(center.x() + 7, center.y() + 9), rx + 6, ry + 6)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w, h, cx, cy, r = self._layout()

        # ------------------------------------------------------------------
        # CHASSIS
        # ------------------------------------------------------------------
        p.fillRect(self.rect(), QColor("#090a0d"))

        deck = QRectF(8, 8, w - 16, h - 16)
        gradient = QLinearGradient(0, 8, 0, h - 8)
        gradient.setColorAt(0.0, QColor("#292b31"))
        gradient.setColorAt(0.45, QColor("#191a1f"))
        gradient.setColorAt(1.0, QColor("#101116"))
        p.setBrush(QBrush(gradient))
        p.setPen(QPen(QColor("#454750"), 2))
        p.drawRoundedRect(deck, 18, 18)

        inner = QRectF(17, 17, w - 34, h - 34)
        p.setBrush(QBrush(QColor("#111217")))
        p.setPen(QPen(QColor("#07080a"), 2))
        p.drawRoundedRect(inner, 14, 14)

        panel = QRectF(28, 28, w - 56, h - 56)
        p.setBrush(QBrush(QColor("#17181d")))
        p.setPen(QPen(QColor("#30323a"), 1))
        p.drawRoundedRect(panel, 11, 11)

        self._text(
            p,
            QRectF(42, 35, 350, 22),
            "KID ACID'S VINYL VAULT",
            12,
            QColor("#d84b91"),
            QFont.Weight.Black,
        )
        self._text(
            p,
            QRectF(42, 57, 390, 17),
            "MP3 SHOWCASE / PROFESSIONAL DIRECT DRIVE",
            8,
        )

        # Decorative screws and inset seams.
        for x, y in ((43, 82), (w - 43, 82), (43, h - 80), (w - 43, h - 80)):
            p.setBrush(QBrush(QColor("#4d4f57")))
            p.setPen(QPen(QColor("#090a0c"), 2))
            p.drawEllipse(QPointF(x, y), 5, 5)
            p.setPen(QPen(QColor("#8b8d95"), 1))
            p.drawLine(QPointF(x - 2, y), QPointF(x + 2, y))

        # ------------------------------------------------------------------
        # PLATTER + VINYL
        # ------------------------------------------------------------------
        self._draw_shadowed_ellipse(p, QPointF(cx, cy), r + 17, r + 17)

        platter_gradient = QRadialGradient(QPointF(cx - r * 0.25, cy - r * 0.25), r + 20)
        platter_gradient.setColorAt(0.0, QColor("#555861"))
        platter_gradient.setColorAt(0.62, QColor("#303239"))
        platter_gradient.setColorAt(1.0, QColor("#17181d"))
        p.setBrush(QBrush(platter_gradient))
        p.setPen(QPen(QColor("#08090b"), 3))
        p.drawEllipse(QPointF(cx, cy), r + 18, r + 18)

        p.setBrush(QBrush(QColor("#22242a")))
        p.setPen(QPen(QColor("#676a73"), 2))
        p.drawEllipse(QPointF(cx, cy), r + 10, r + 10)

        # Strobe dots rotate subtly with the platter.
        for i in range(60):
            a = math.radians(i * 6.0 + self.angle * 0.16)
            rr = r + 5
            dot = QPointF(cx + math.cos(a) * rr, cy + math.sin(a) * rr)
            major = i % 5 == 0
            p.setPen(QPen(QColor("#a6a8af"), 2.5 if major else 1.4))
            p.drawPoint(dot)

        # Record shadow.
        p.setBrush(QBrush(QColor(0, 0, 0, 150)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx + 3, cy + 4), r, r)

        record_gradient = QRadialGradient(QPointF(cx - r * 0.35, cy - r * 0.35), r * 1.05)
        record_gradient.setColorAt(0.0, QColor("#24262b"))
        record_gradient.setColorAt(0.18, QColor("#0d0e11"))
        record_gradient.setColorAt(0.78, QColor("#030406"))
        record_gradient.setColorAt(1.0, QColor("#111217"))
        p.setBrush(QBrush(record_gradient))
        p.setPen(QPen(QColor("#050609"), 2))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # Grooves and moving highlight.
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for factor in (0.985, 0.965, 0.945, 0.925, 0.905, 0.885, 0.865,
                       0.845, 0.825, 0.805, 0.785, 0.765, 0.745, 0.725,
                       0.705, 0.685, 0.665, 0.645, 0.625, 0.605):
            p.setPen(QPen(QColor(70, 72, 78, 90), 1))
            p.drawEllipse(QPointF(0, 0), r * factor, r * factor)

        p.setPen(QPen(QColor(225, 225, 230, 24), 3))
        p.drawArc(QRectF(-r * 0.88, -r * 0.88, r * 1.76, r * 1.76), 12 * 16, 55 * 16)
        p.setPen(QPen(QColor(216, 75, 145, 85), 2))
        p.drawArc(QRectF(-r * 0.73, -r * 0.73, r * 1.46, r * 1.46), 198 * 16, 38 * 16)
        p.restore()

        # Label and spindle.
        label_r = min(61.0, r * 0.255)
        label_gradient = QRadialGradient(QPointF(cx - label_r * 0.25, cy - label_r * 0.25), label_r)
        label_gradient.setColorAt(0.0, QColor("#b94b7d"))
        label_gradient.setColorAt(0.72, QColor("#711b45"))
        label_gradient.setColorAt(1.0, QColor("#45102b"))
        p.setBrush(QBrush(label_gradient))
        p.setPen(QPen(QColor("#ef9fc2"), 2))
        p.drawEllipse(QPointF(cx, cy), label_r, label_r)
        p.setPen(QPen(QColor("#e2a1be"), 1))
        p.drawEllipse(QPointF(cx, cy), label_r * 0.78, label_r * 0.78)
        self._text(
            p,
            QRectF(cx - label_r, cy - 11, label_r * 2, 18),
            "KID ACID",
            max(8, int(label_r * 0.15)),
            QColor("#f8e9f0"),
            QFont.Weight.Black,
            Qt.AlignmentFlag.AlignCenter,
        )
        self._text(
            p,
            QRectF(cx - label_r, cy + 7, label_r * 2, 15),
            "VINYL VAULT",
            max(5, int(label_r * 0.075)),
            QColor("#edb2ca"),
            QFont.Weight.Bold,
            Qt.AlignmentFlag.AlignCenter,
        )
        p.setBrush(QBrush(QColor("#cfd0d5")))
        p.setPen(QPen(QColor("#6e7078"), 1))
        p.drawEllipse(QPointF(cx, cy), 5.5, 5.5)
        p.setBrush(QBrush(QColor("#17181c")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 2.2, 2.2)

        # ------------------------------------------------------------------
        # TONEARM: LONG, MECHANICAL, WITH A REAL REST CRADLE
        # ------------------------------------------------------------------
        pivot = QPointF(w - 112, 122)
        rest_stylus = QPointF(cx + r + 48, cy - r * 0.31)
        play_stylus = QPointF(cx + r * 0.68, cy + r * 0.10)
        stylus = self._lerp(rest_stylus, play_stylus, self.arm_progress)

        # Cradle remains visible at the true rest position.
        cradle = QPointF(rest_stylus.x() + 5, rest_stylus.y() - 2)
        p.setPen(QPen(QColor("#07080a"), 3))
        p.setBrush(QBrush(QColor("#25272d")))
        p.drawRoundedRect(QRectF(cradle.x() - 18, cradle.y() - 13, 36, 26), 5, 5)
        p.setPen(QPen(QColor("#62656e"), 2))
        p.drawLine(QPointF(cradle.x() - 10, cradle.y() - 6), QPointF(cradle.x() + 10, cradle.y() - 6))
        p.drawLine(QPointF(cradle.x() - 10, cradle.y() + 6), QPointF(cradle.x() + 10, cradle.y() + 6))
        p.setPen(QPen(QColor("#9699a1"), 1))
        p.drawLine(QPointF(cradle.x() - 12, cradle.y()), QPointF(cradle.x() + 12, cradle.y()))

        # Geometry for the long S-shaped arm. The stylus end follows the
        # platter naturally while the pivot stays fixed.
        dx = stylus.x() - pivot.x()
        dy = stylus.y() - pivot.y()
        arm_angle = math.degrees(math.atan2(dy, dx))
        length = max(1.0, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        perp = QPointF(-uy, ux)

        elbow = QPointF(
            pivot.x() + dx * 0.55 + perp.x() * 20,
            pivot.y() + dy * 0.55 + perp.y() * 20,
        )
        headshell_center = QPointF(
            stylus.x() - ux * 25,
            stylus.y() - uy * 25,
        )

        # Counterweight is behind the pivot and stays mechanically attached.
        counter = QPointF(pivot.x() - 48, pivot.y() - 2)
        p.setPen(QPen(QColor("#07080a"), 17, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, counter)
        p.setPen(QPen(QColor("#70737c"), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, counter)
        p.setPen(QPen(QColor("#c4c6cc"), 2))
        p.drawLine(QPointF(pivot.x(), pivot.y() - 3), QPointF(counter.x(), counter.y() - 3))
        p.setBrush(QBrush(QColor("#4a4c53")))
        p.setPen(QPen(QColor("#92959d"), 2))
        p.drawEllipse(counter, 17, 17)
        p.setBrush(QBrush(QColor("#23252a")))
        p.setPen(QPen(QColor("#666972"), 2))
        p.drawEllipse(counter, 10, 10)
        p.setPen(QPen(QColor("#aeb0b7"), 2))
        for offset in (-5, 0, 5):
            p.drawLine(
                QPointF(counter.x() - 13, counter.y() + offset),
                QPointF(counter.x() + 13, counter.y() + offset),
            )

        # Main arm path with dark outline, metal body and highlight.
        arm_path = QPainterPath()
        arm_path.moveTo(pivot)
        arm_path.cubicTo(
            QPointF(pivot.x() - 12, pivot.y() + 5),
            QPointF(elbow.x() + 12, elbow.y() - 8),
            elbow,
        )
        arm_path.cubicTo(
            QPointF(elbow.x() - 15, elbow.y() + 6),
            QPointF(headshell_center.x() + 18, headshell_center.y() - 2),
            headshell_center,
        )
        p.setPen(QPen(QColor("#06070a"), 18, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(arm_path)
        p.setPen(QPen(QColor("#9fa2aa"), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(arm_path)
        p.setPen(QPen(QColor("#e1e2e5"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        highlight = QPainterPath()
        highlight.moveTo(QPointF(pivot.x() - 1, pivot.y() - 2))
        highlight.cubicTo(
            QPointF(pivot.x() + 6, pivot.y() - 1),
            QPointF(elbow.x() + 4, elbow.y() - 9),
            QPointF(elbow.x(), elbow.y() - 2),
        )
        highlight.cubicTo(
            QPointF(elbow.x() - 3, elbow.y() + 1),
            QPointF(headshell_center.x() + 16, headshell_center.y() - 6),
            QPointF(headshell_center.x(), headshell_center.y() - 4),
        )
        p.drawPath(highlight)

        # Headshell follows the arm direction.
        shell = QPointF(
            stylus.x() - ux * 40,
            stylus.y() - uy * 40,
        )
        p.save()
        p.translate(shell)
        p.rotate(arm_angle)
        p.setBrush(QBrush(QColor("#b9bbc1")))
        p.setPen(QPen(QColor("#08090b"), 3))
        p.drawRoundedRect(QRectF(-27, -9, 34, 18), 3, 3)
        p.setBrush(QBrush(QColor("#30323a")))
        p.setPen(QPen(QColor("#70737c"), 1))
        p.drawRoundedRect(QRectF(4, -7, 22, 14), 2, 2)
        p.setBrush(QBrush(QColor("#15161a")))
        p.setPen(QPen(QColor("#868992"), 1))
        p.drawRect(QRectF(9, -5, 13, 10))
        p.setBrush(QBrush(QColor("#d5d6da")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(12, -3.5), 1.5, 1.5)
        p.drawEllipse(QPointF(12, 3.5), 1.5, 1.5)
        p.restore()

        # Cartridge body and stylus assembly.
        cartridge = QPointF(stylus.x() - ux * 12, stylus.y() - uy * 12)
        p.save()
        p.translate(cartridge)
        p.rotate(arm_angle)
        p.setBrush(QBrush(QColor("#15161a")))
        p.setPen(QPen(QColor("#8f929a"), 1))
        p.drawRoundedRect(QRectF(-6, -5, 16, 10), 2, 2)
        p.setBrush(QBrush(QColor("#d84b91")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(QRectF(5, -3, 4, 6))
        p.restore()

        # Stylus is explicitly drawn to the record surface.
        stylus_base = QPointF(stylus.x() - ux * 6, stylus.y() - uy * 6)
        stylus_tip = QPointF(stylus.x() + ux * 3, stylus.y() + uy * 3)
        p.setPen(QPen(QColor("#08090b"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(stylus_base, stylus_tip)
        p.setPen(QPen(QColor("#f1f2f4"), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(stylus_base, stylus_tip)
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(stylus_tip, 2.2, 2.2)

        # Pivot housing, drawn last so it sits visibly above the arm tube.
        pivot_gradient = QRadialGradient(QPointF(pivot.x() - 7, pivot.y() - 7), 25)
        pivot_gradient.setColorAt(0.0, QColor("#777a82"))
        pivot_gradient.setColorAt(0.65, QColor("#3a3c43"))
        pivot_gradient.setColorAt(1.0, QColor("#17181d"))
        p.setBrush(QBrush(pivot_gradient))
        p.setPen(QPen(QColor("#07080a"), 4))
        p.drawEllipse(pivot, 27, 27)
        p.setBrush(QBrush(QColor("#202228")))
        p.setPen(QPen(QColor("#777a83"), 2))
        p.drawEllipse(pivot, 17, 17)
        p.setBrush(QBrush(QColor("#c4c6ca")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(pivot, 4, 4)
        p.setPen(QPen(QColor("#8f9299"), 1))
        p.drawLine(QPointF(pivot.x() - 8, pivot.y()), QPointF(pivot.x() + 8, pivot.y()))
        p.drawLine(QPointF(pivot.x(), pivot.y() - 8), QPointF(pivot.x(), pivot.y() + 8))

        # Cueing lever and lock mechanism.
        cue_x = w - 55
        cue_y = 210
        p.setPen(QPen(QColor("#686b73"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(cue_x, cue_y + 25), QPointF(cue_x, cue_y - 5))
        p.setPen(QPen(QColor("#a5a7ad"), 2))
        p.drawLine(QPointF(cue_x - 7, cue_y - 8), QPointF(cue_x + 8, cue_y - 8))
        p.setBrush(QBrush(QColor("#2b2d33")))
        p.setPen(QPen(QColor("#70737b"), 1))
        p.drawRoundedRect(QRectF(cue_x - 8, cue_y + 21, 16, 9), 3, 3)

        # ------------------------------------------------------------------
        # LEFT PITCH CONTROL
        # ------------------------------------------------------------------
        pitch_x = 48
        top = 210
        bottom = max(top + 150, h - 155)
        center = (top + bottom) / 2
        p.setPen(QPen(QColor("#07080a"), 11))
        p.drawLine(QPointF(pitch_x, top), QPointF(pitch_x, bottom))
        p.setPen(QPen(QColor("#777a82"), 3))
        p.drawLine(QPointF(pitch_x, top), QPointF(pitch_x, bottom))
        step = (bottom - top) / 16.0
        for i in range(-8, 9):
            y = center - i * step
            major = i in (-8, -4, 0, 4, 8)
            p.setPen(QPen(QColor("#b6b8be") if major else QColor("#5c5f67"), 2))
            tick = 17 if major else 9
            p.drawLine(QPointF(pitch_x - tick, y), QPointF(pitch_x + tick, y))
        knob_y = center - max(-8.0, min(8.0, self.pitch)) * step
        p.setBrush(QBrush(QColor("#c7c9ce")))
        p.setPen(QPen(QColor("#07080a"), 3))
        p.drawRoundedRect(QRectF(pitch_x - 25, knob_y - 11, 50, 22), 5, 5)
        p.setPen(QPen(QColor("#6d7078"), 1))
        p.drawLine(QPointF(pitch_x - 17, knob_y), QPointF(pitch_x + 17, knob_y))
        self._text(p, QRectF(pitch_x - 35, top - 28, 70, 18), "+8", 8, align=Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(pitch_x - 35, center - 9, 70, 18), "0", 8, QColor("#f2f2f5"), QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(pitch_x - 35, bottom + 9, 70, 18), "-8", 8, align=Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(pitch_x - 42, bottom + 30, 84, 18), "PITCH", 8, QColor("#d84b91"), QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------------------------------
        # POWER + INFORMATION STRIP
        # ------------------------------------------------------------------
        power = QPointF(70, h - 66)
        p.setBrush(QBrush(QColor("#292b31")))
        p.setPen(QPen(QColor("#050607"), 3))
        p.drawEllipse(power, 24, 24)
        p.setPen(QPen(QColor("#5c5f68"), 1))
        p.drawEllipse(power, 19, 19)
        p.setPen(QPen(QColor("#d84b91") if self.power_on else QColor("#5a5c63"), 3))
        p.drawArc(QRectF(power.x() - 11, power.y() - 11, 22, 22), 45 * 16, 270 * 16)
        p.drawLine(QPointF(power.x(), power.y() - 14), QPointF(power.x(), power.y() + 1))
        self._text(p, QRectF(power.x() - 40, power.y() + 27, 80, 18), "POWER", 7, QColor("#d84b91") if self.power_on else QColor("#777981"), QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)

        strip = QRectF(120, h - 92, max(260.0, w - 205), 58)
        p.setBrush(QBrush(QColor("#0c0d11")))
        p.setPen(QPen(QColor("#30323a"), 1))
        p.drawRoundedRect(strip, 7, 7)
        self._text(p, QRectF(strip.x() + 12, strip.y() + 6, strip.width() - 24, 17), "33 RPM | DIRECT DRIVE | STABLE PLATTER", 8)
        self._text(p, QRectF(strip.x() + 12, strip.y() + 27, strip.width() * 0.44, 20), self.artist, 10, QColor("#f2f2f5"), QFont.Weight.Bold)
        self._text(p, QRectF(strip.x() + strip.width() * 0.46, strip.y() + 27, strip.width() * 0.51 - 12, 20), self.title, 10, QColor("#d84b91"), QFont.Weight.Black, Qt.AlignmentFlag.AlignRight)

        # Small status light.
        status = QColor("#77d999") if self.playing else QColor("#777981")
        p.setBrush(QBrush(status))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(w - 46, h - 64), 4, 4)
        self._text(p, QRectF(w - 92, h - 55, 45, 18), "PLAY" if self.playing else "READY", 7, status, QFont.Weight.Black, Qt.AlignmentFlag.AlignRight)

        p.end()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        w, h, *_ = self._layout()
        pos = event.position()
        power = QPointF(70, h - 66)
        if math.hypot(pos.x() - power.x(), pos.y() - power.y()) <= 32:
            self.set_power(not self.power_on)
            event.accept()
            return
        super().mousePressEvent(event)


class MP3ShowcasePage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.visible_items = []
        self.current_index = -1
        self.build_ui()
        self.load_files()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        title = QLabel("MP3 SHOWCASE")
        title.setStyleSheet("font-size:26px;font-weight:900;color:#fff;")
        root.addWidget(title)

        search = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand...")
        search.addWidget(self.search, 1)
        self.refresh = QPushButton("VERVERS")
        search.addWidget(self.refresh)
        root.addLayout(search)

        self.status = QLabel("0 MP3's")
        self.status.setStyleSheet("color:#9b9ba6;")
        root.addWidget(self.status)

        body = QHBoxLayout()
        body.setSpacing(20)

        self.list = QListWidget()
        self.list.setMinimumWidth(360)
        self.list.currentRowChanged.connect(self.select_index)
        body.addWidget(self.list)

        card = QFrame()
        card.setStyleSheet("QFrame{background:#121219;border:1px solid #2a2532;border-radius:10px;}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 22, 22, 22)
        cl.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(22)

        self.cover = QLabel("NO COVER")
        self.cover.setFixedSize(340, 340)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setStyleSheet("background:#0b0b0f;color:#666672;border:1px solid #302b39;border-radius:6px;")
        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)
        self.artist_label = QLabel("-")
        self.artist_label.setStyleSheet("color:#d84b91;font-size:18px;font-weight:bold;")
        self.artist_label.setWordWrap(True)
        info.addWidget(self.artist_label)
        self.title_label = QLabel("-")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color:#fff;font-size:27px;font-weight:800;")
        info.addWidget(self.title_label)
        self.meta_label = QLabel("-")
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet("color:#aaaab3;font-size:13px;")
        info.addWidget(self.meta_label)
        self.release_label = QLabel("Release: -")
        self.release_label.setWordWrap(True)
        self.release_label.setStyleSheet("color:#c5b6d4;font-size:14px;font-weight:bold;")
        info.addWidget(self.release_label)
        self.discogs_label = QLabel("Discogs: -")
        self.discogs_label.setWordWrap(True)
        self.discogs_label.setStyleSheet("color:#8f8798;font-size:12px;")
        info.addWidget(self.discogs_label)
        self.comment_label = QLabel("")
        self.comment_label.setWordWrap(True)
        self.comment_label.setStyleSheet("color:#777783;font-size:12px;")
        info.addWidget(self.comment_label)
        info.addStretch()
        top.addLayout(info, 1)
        cl.addLayout(top)

        self.vinyl_deck = VinylDeckWidget(self)
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)
        cl.addWidget(self.vinyl_deck, 1)

        controls = QHBoxLayout()
        self.previous = QPushButton("< VORIGE")
        self.play = QPushButton("> PLAY")
        self.next = QPushButton("VOLGENDE >")
        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        cl.addLayout(controls)

        tracks_title = QLabel("TRACKS")
        tracks_title.setStyleSheet("color:#777783;font-size:11px;font-weight:bold;letter-spacing:1.5px;")
        cl.addWidget(tracks_title)
        self.track_list = QListWidget()
        self.track_list.setMinimumHeight(190)
        self.track_list.itemDoubleClicked.connect(self.play_track_item)
        cl.addWidget(self.track_list, 1)

        body.addWidget(card, 1)
        root.addLayout(body, 1)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.populate_list)
        self.search.textChanged.connect(lambda _: self.timer.start())
        self.refresh.clicked.connect(self.load_files)
        self.previous.clicked.connect(self.previous_track)
        self.next.clicked.connect(self.next_track)
        self.play.clicked.connect(self.play_current)

        self.setStyleSheet("""
            QWidget{background:#0b0b0f;color:#f2f2f5;}
            QLineEdit,QPushButton,QListWidget{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;}
            QPushButton{font-weight:800;min-height:32px;}
            QPushButton:hover{border-color:#d84b91;background:#24242c;}
            QListWidget{background:#0f0f14;}
            QListWidget::item{padding:8px;border-bottom:1px solid #24242d;}
            QListWidget::item:selected{background:#271522;border:1px solid #5d2947;}
        """)

    def load_files(self):
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT m.path,m.artist,m.title,m.album,m.year,m.bpm,m.genre,
                       COALESCE(r.artist,''),COALESCE(r.title,''),COALESCE(r.discogs,''),COALESCE(r.cover,'')
                FROM mp3_files m
                LEFT JOIN track_mp3 tm ON tm.mp3_id=m.id
                LEFT JOIN tracks t ON t.id=tm.track_id
                LEFT JOIN releases r ON r.id=t.release_id
                ORDER BY m.artist COLLATE NOCASE,m.title COLLATE NOCASE,m.path COLLATE NOCASE
            """).fetchall()
        finally:
            conn.close()

        unique = {}
        for row in rows:
            path = str(row[0] or "")
            if path not in unique:
                unique[path] = tuple(row)
            elif not unique[path][9] and row[9]:
                unique[path] = tuple(row)
        self.items = list(unique.values())
        self.populate_list()

    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [
            row for row in self.items
            if not q or q in " ".join(str(x or "") for x in row).casefold()
        ]
        self.list.blockSignals(True)
        self.list.clear()
        for row in self.visible_items:
            name = Path(str(row[0])).name
            artist = str(row[1] or "").strip()
            title = str(row[2] or "").strip()
            if artist or title:
                text = f"{artist} - {title}".strip(" -")
            else:
                text = name
            item = QListWidgetItem(text)
            item.setToolTip(str(row[0]))
            self.list.addItem(item)
        self.list.blockSignals(False)
        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items:
            self.list.setCurrentRow(0)
        else:
            self.current_index = -1
            self.clear_showcase()

    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            self.show_item(self.visible_items[index])

    def show_item(self, row):
        path, artist, title, album, year, bpm, genre, release_artist, release_title, discogs_id, release_cover = row
        artist = str(artist or "").strip() or "Onbekende artiest"
        title = str(title or "").strip() or Path(str(path)).stem
        album = str(album or "").strip()
        self.artist_label.setText(artist)
        self.title_label.setText(title)
        meta = []
        if album:
            meta.append(f"Album: {album}")
        if year:
            meta.append(f"Jaar: {year}")
        if genre:
            meta.append(f"Genre: {genre}")
        if bpm:
            meta.append(f"BPM: {bpm}")
        self.meta_label.setText("  |  ".join(meta) if meta else "Geen aanvullende metadata")
        if release_title:
            release_text = str(release_title)
            if release_artist:
                release_text = f"{release_artist} - {release_text}"
            self.release_label.setText(f"Release: {release_text}")
        else:
            self.release_label.setText("Release: geen gekoppelde release")
        self.discogs_label.setText(
            f"Discogs release ID: {discogs_id}" if discogs_id else "Discogs: geen releasekoppeling"
        )
        self.vinyl_deck.set_track(artist, title)
        self.vinyl_deck.set_playing(False)
        self.load_cover(str(path), str(release_cover or ""))
        self.load_tracklist(str(path))
        self.load_comment(str(path))
        self.previous.setEnabled(self.current_index > 0)
        self.next.setEnabled(self.current_index + 1 < len(self.visible_items))
        self.play.setEnabled(True)

    def load_cover(self, path, release_cover):
        if MUTAGEN_AVAILABLE and Path(path).exists():
            try:
                tags = ID3(path)
                pictures = tags.getall("APIC")
                if pictures:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(pictures[0].data):
                        self.cover.setPixmap(
                            pixmap.scaled(
                                340,
                                340,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
                        self.cover.setText("")
                        return
            except Exception:
                pass
        if release_cover and Path(release_cover).exists():
            pixmap = QPixmap(release_cover)
            if not pixmap.isNull():
                self.cover.setPixmap(
                    pixmap.scaled(
                        340,
                        340,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.cover.setText("")
                return
        self.cover.clear()
        self.cover.setText("NO COVER")

    def load_comment(self, path):
        self.comment_label.clear()
        if not MUTAGEN_AVAILABLE or not Path(path).exists():
            return
        try:
            tags = ID3(path)
            values = []
            for frame in tags.getall("COMM"):
                values.extend(str(value).strip() for value in frame.text if str(value).strip())
            if values:
                self.comment_label.setText("Comment: " + " | ".join(dict.fromkeys(values)))
        except Exception:
            pass

    def load_tracklist(self, current_path):
        self.track_list.clear()
        try:
            conn = get_connection()
            try:
                linked = conn.execute("""
                    SELECT t.position,t.title,t.duration,t.bpm,m.path
                    FROM track_mp3 tm
                    JOIN tracks t ON t.id=tm.track_id
                    JOIN mp3_files m ON m.id=tm.mp3_id
                    WHERE m.path=?
                    ORDER BY t.position COLLATE NOCASE
                """, (current_path,)).fetchall()
            finally:
                conn.close()
        except Exception:
            linked = []
        if not linked:
            item = QListWidgetItem("Geen gekoppelde VinylVault-track voor dit bestand")
            item.setForeground(Qt.GlobalColor.gray)
            self.track_list.addItem(item)
            return
        for position, title, duration, bpm, path in linked:
            text = f"{position or ''}  {title or ''}".strip()
            extras = []
            if duration:
                extras.append(str(duration))
            if bpm:
                extras.append(f"{bpm} BPM")
            if extras:
                text += "  |  " + "  |  ".join(extras)
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.track_list.addItem(item)

    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.vinyl_deck.set_playing(True)
                self.play_mp3.emit(path)

    def play_track_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(str(path)).exists():
            self.vinyl_deck.set_track(self.artist_label.text(), self.title_label.text())
            self.vinyl_deck.set_playing(True)
            self.play_mp3.emit(str(path))
        else:
            self.play_current()

    def previous_track(self):
        if self.current_index > 0:
            self.list.setCurrentRow(self.current_index - 1)
            self.play_current()

    def next_track(self):
        if self.current_index + 1 < len(self.visible_items):
            self.list.setCurrentRow(self.current_index + 1)
            self.play_current()

    def clear_showcase(self):
        self.cover.clear()
        self.cover.setText("NO COVER")
        self.artist_label.setText("-")
        self.title_label.setText("-")
        self.meta_label.setText("-")
        self.release_label.setText("Release: -")
        self.discogs_label.setText("Discogs: -")
        self.comment_label.clear()
        self.track_list.clear()
        self.previous.setEnabled(False)
        self.next.setEnabled(False)
        self.play.setEnabled(False)
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)
