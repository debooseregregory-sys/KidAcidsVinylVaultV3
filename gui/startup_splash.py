from __future__ import annotations

import math

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from PySide6.QtWidgets import QWidget


class StartupSplash(QWidget):
    """Fullscreen-style frameless startup announcement for MusicVault."""

    def __init__(self, duration=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(980, 560)

        self._phase = 0.0
        self._elapsed = 0
        self._duration = duration
        self._fade = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(20)

    def showEvent(self, event):
        super().showEvent(event)
        screen = self.screen()
        if screen:
            area = screen.availableGeometry()
            self.move(
                area.center().x() - self.width() // 2,
                area.center().y() - self.height() // 2,
            )
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(650)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()

    def _animate(self):
        self._elapsed += 20
        self._phase += 0.045
        self.update()

        # When duration is None, the splash stays visible until the
        # application explicitly closes it after the main window is ready.
        if self._duration is None:
            return

        if self._elapsed >= self._duration:
            self._timer.stop()
            self._fade = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade.setDuration(500)
            self._fade.setStartValue(self.windowOpacity())
            self._fade.setEndValue(0.0)
            self._fade.setEasingCurve(QEasingCurve.Type.InCubic)
            self._fade.finished.connect(self.close)
            self._fade.start()

    def paintEvent(self, event):
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        w, h = r.width(), r.height()
        cx, cy = r.center().x(), r.center().y() + 28

        bg = QLinearGradient(r.left(), r.top(), r.right(), r.bottom())
        bg.setColorAt(0.0, QColor(2, 2, 8, 253))
        bg.setColorAt(0.38, QColor(24, 2, 27, 253))
        bg.setColorAt(0.62, QColor(7, 3, 20, 253))
        bg.setColorAt(1.0, QColor(1, 2, 7, 253))
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(255, 45, 190, 210), 2))
        p.drawRoundedRect(r, 28, 28)

        p.setPen(QPen(QColor(255, 80, 210, 14), 1))
        scan_shift = int((self._phase * 34) % 12)
        for y in range(r.top() + scan_shift, r.bottom(), 12):
            p.drawLine(r.left() + 18, y, r.right() - 18, y)

        glow_radius = 250 + int(18 * math.sin(self._phase * 1.7))
        for i in range(7, 0, -1):
            radius = glow_radius * i / 7
            alpha = 7 + i * 3
            p.setBrush(QBrush(QColor(255, 20, 190, alpha)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        pulse = 14 + 12 * (0.5 + 0.5 * math.sin(self._phase * 2))
        for i in range(8):
            radius = 72 + i * 32 + pulse
            alpha = max(15, 125 - i * 14)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(255, 35, 190, alpha), 2 if i < 2 else 1))
            p.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        for i in range(20):
            a = self._phase * 1.7 + i * math.tau / 20
            inner = 38
            outer = 88 + 12 * math.sin(self._phase * 3 + i * 0.8)
            alpha = 150 + int(70 * (0.5 + 0.5 * math.sin(a * 2)))
            p.setPen(QPen(QColor(255, 48, 198, alpha), 2.5))
            p.drawLine(
                int(cx + math.cos(a) * inner),
                int(cy + math.sin(a) * inner),
                int(cx + math.cos(a) * outer),
                int(cy + math.sin(a) * outer),
            )

        p.setBrush(QBrush(QColor(7, 7, 12, 235)))
        p.setPen(QPen(QColor(255, 70, 205, 180), 2))
        p.drawEllipse(int(cx - 48), int(cy - 48), 96, 96)
        p.setPen(QPen(QColor(110, 80, 125, 120), 1))
        for rr in (32, 38, 44):
            p.drawEllipse(int(cx - rr), int(cy - rr), rr * 2, rr * 2)
        p.setBrush(QBrush(QColor(255, 45, 195, 235)))
        p.setPen(QPen(QColor(255, 230, 250), 2))
        p.drawEllipse(int(cx - 8), int(cy - 8), 16, 16)

        for i in range(110):
            a = self._phase * (0.22 + (i % 9) * 0.035) + i * 0.37
            ox = w * (0.17 + (i % 7) * 0.065)
            oy = h * (0.14 + (i % 6) * 0.055)
            x = cx + math.sin(a * 0.91 + i) * ox
            y = cy + math.cos(a * 1.07 + i * 0.19) * oy
            size = 0.7 + 2.5 * (0.5 + 0.5 * math.sin(a * 2.4 + i))
            alpha = 65 + int(150 * (0.5 + 0.5 * math.sin(a + i)))
            p.setBrush(QBrush(QColor(255, 55, 205, alpha)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(x - size), int(y - size), int(size * 2), int(size * 2))

        bar_count = 76
        base_y = r.bottom() - 82
        step = (w - 90) / bar_count
        for i in range(bar_count):
            wave = (
                math.sin(self._phase * 3.0 + i * 0.31)
                + 0.55 * math.sin(self._phase * 5.4 - i * 0.19)
                + 0.25 * math.sin(self._phase * 1.6 + i * 0.71)
            ) / 1.8
            height = 5 + (wave + 1.0) * 18
            x = r.left() + 45 + i * step
            p.setPen(QPen(QColor(255, 48, 195, 125), max(1.5, step * 0.34)))
            p.drawLine(int(x), int(base_y), int(x), int(base_y - height))

        p.setPen(QPen(QColor(255, 218, 244)))
        p.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        label = "WELCOME TO"
        tw = p.fontMetrics().horizontalAdvance(label)
        p.drawText(int(cx - tw / 2), 70, label)

        title = "KID ACID'S"
        p.setFont(QFont("Arial", 39, QFont.Weight.Black))
        tw = p.fontMetrics().horizontalAdvance(title)
        p.setPen(QPen(QColor(255, 255, 255)))
        p.drawText(int(cx - tw / 2), 116, title)

        title2 = "MUSICVAULT"
        p.setFont(QFont("Arial", 49, QFont.Weight.Black))
        tw = p.fontMetrics().horizontalAdvance(title2)
        glow = 105 + int(85 * (0.5 + 0.5 * math.sin(self._phase * 2)))
        p.setPen(QPen(QColor(255, 40, 195, glow), 3))
        p.drawText(int(cx - tw / 2), 168, title2)
        p.setPen(QPen(QColor(255, 248, 255)))
        p.drawText(int(cx - tw / 2), 168, title2)

        line_width = 120 + int(90 * (0.5 + 0.5 * math.sin(self._phase * 2.5)))
        p.setPen(QPen(QColor(255, 55, 200, 210), 2))
        p.drawLine(int(cx - line_width / 2), 186, int(cx + line_width / 2), 186)

        p.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        p.setPen(QPen(QColor(205, 175, 210)))
        sub = "VINYL  •  CD  •  MP3  •  LIVESETS"
        tw = p.fontMetrics().horizontalAdvance(sub)
        p.drawText(int(cx - tw / 2), h - 54, sub)

        p.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        p.setPen(QPen(QColor(120, 115, 140)))
        status = "INITIALIZING YOUR MUSIC COLLECTION"
        tw = p.fontMetrics().horizontalAdvance(status)
        p.drawText(int(cx - tw / 2), h - 32, status)

        p.end()
