from __future__ import annotations

import math

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from PySide6.QtWidgets import QWidget


class StartupSplash(QWidget):
    """Fullscreen-style frameless startup announcement for MusicVault."""

    def __init__(self, duration=3200, parent=None):
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
        cx, cy = r.center().x(), r.center().y() + 18

        bg = QLinearGradient(r.left(), r.top(), r.right(), r.bottom())
        bg.setColorAt(0.0, QColor(3, 2, 8, 252))
        bg.setColorAt(0.45, QColor(30, 3, 31, 252))
        bg.setColorAt(0.7, QColor(8, 2, 18, 252))
        bg.setColorAt(1.0, QColor(2, 2, 6, 252))
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(255, 45, 190, 210), 2))
        p.drawRoundedRect(r, 28, 28)

        # Pulsing neon rings.
        pulse = 18 + 10 * (0.5 + 0.5 * math.sin(self._phase * 2))
        for i in range(9):
            radius = 90 + i * 34 + pulse
            alpha = max(18, 130 - i * 12)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(255, 30, 190, alpha), 2 if i < 3 else 1))
            p.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        # Orbiting particles.
        for i in range(90):
            a = self._phase * (0.25 + (i % 7) * 0.045) + i * 0.42
            ox = w * (0.20 + (i % 6) * 0.07)
            oy = h * (0.18 + (i % 5) * 0.055)
            x = cx + math.sin(a * 0.9 + i) * ox
            y = cy + math.cos(a * 1.15 + i * 0.13) * oy
            size = 1.0 + 2.8 * (0.5 + 0.5 * math.sin(a * 2.2 + i))
            p.setBrush(QBrush(QColor(255, 50, 205, 100 + int(120 * (0.5 + 0.5 * math.sin(a))))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(x - size), int(y - size), int(size * 2), int(size * 2))

        # Central energy core.
        for i in range(24):
            a = self._phase * 2.1 + i * math.tau / 24
            inner = 28
            outer = 70 + 18 * math.sin(self._phase * 3 + i * 0.7)
            p.setPen(QPen(QColor(255, 45, 195, 190), 3))
            p.drawLine(
                int(cx + math.cos(a) * inner),
                int(cy + math.sin(a) * inner),
                int(cx + math.cos(a) * outer),
                int(cy + math.sin(a) * outer),
            )
        p.setBrush(QBrush(QColor(255, 45, 200, 230)))
        p.setPen(QPen(QColor(255, 220, 250), 2))
        p.drawEllipse(int(cx - 17), int(cy - 17), 34, 34)

        # Announcement text.
        p.setPen(QPen(QColor(255, 220, 246)))
        p.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        label = "WELCOME TO"
        tw = p.fontMetrics().horizontalAdvance(label)
        p.drawText(int(cx - tw / 2), 76, label)

        title = "KID ACID'S"
        p.setFont(QFont("Arial", 52, QFont.Weight.Black))
        tw = p.fontMetrics().horizontalAdvance(title)
        p.setPen(QPen(QColor(255, 255, 255)))
        p.drawText(int(cx - tw / 2), 132, title)

        title2 = "MUSICVAULT"
        p.setFont(QFont("Arial", 64, QFont.Weight.Black))
        tw = p.fontMetrics().horizontalAdvance(title2)
        glow = 130 + int(80 * (0.5 + 0.5 * math.sin(self._phase * 2)))
        p.setPen(QPen(QColor(255, 45, 195, glow), 2))
        p.drawText(int(cx - tw / 2), 198, title2)
        p.setPen(QPen(QColor(255, 245, 255)))
        p.drawText(int(cx - tw / 2), 198, title2)

        p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        p.setPen(QPen(QColor(210, 180, 210)))
        sub = "VINYL  •  CD  •  MP3  •  LIVESETS"
        tw = p.fontMetrics().horizontalAdvance(sub)
        p.drawText(int(cx - tw / 2), h - 82, sub)

        p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        p.setPen(QPen(QColor(130, 125, 145)))
        status = "LOADING YOUR MUSIC COLLECTION  •  PLEASE WAIT"
        tw = p.fontMetrics().horizontalAdvance(status)
        p.drawText(int(cx - tw / 2), h - 50, status)

        p.end()
