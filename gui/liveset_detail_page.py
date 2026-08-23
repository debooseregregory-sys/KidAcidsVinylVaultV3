from __future__ import annotations

from gui.app_settings import paint_accent

import math
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QFont, QLinearGradient, QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class LivesetPlayerVisualizer(QWidget):
    """Large animated visual tied to the liveset that is actually loaded."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(430)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        self._phase = 0.0
        self._text_offset = 0.0
        self._artist = ""
        self._title = ""
        self._playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(24)

    def set_now_playing(self, artist: str, title: str, playing: bool):
        self._artist = str(artist or "").strip()
        self._title = str(title or "").strip()
        self._playing = bool(playing)
        self.update()

    def _animate(self):
        self._phase = (self._phase + (0.085 if self._playing else 0.032)) % (math.pi * 2)
        self._text_offset = (self._text_offset + (3.4 if self._playing else 1.0)) % 5000
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        w, h = rect.width(), rect.height()
        cx = rect.center().x()
        cy = rect.top() + h * 0.54

        # Dark club-like backdrop.
        bg = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        bg.setColorAt(0.0, QColor(3, 3, 7))
        bg.setColorAt(0.30, QColor(34, 3, 35))
        bg.setColorAt(0.52, QColor(8, 2, 15))
        bg.setColorAt(0.78, QColor(28, 3, 30))
        bg.setColorAt(1.0, QColor(2, 2, 6))
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor(110, 20, 105), 2))
        painter.drawRoundedRect(rect, 24, 24)

        # Huge atmospheric glow layers.
        for radius, alpha in ((310, 18), (250, 24), (190, 32), (135, 45)):
            painter.setBrush(QBrush(QColor(255, 0, 190, alpha)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(cx - radius), int(cy - radius), radius * 2, radius * 2)

        # Rotating outer orbital arcs.
        orbit_radius = min(w, h) * (0.29 if self._playing else 0.25)
        for i in range(10):
            radius = orbit_radius + i * 16
            span = 34 + 8 * math.sin(self._phase * 1.7 + i)
            start = int((self._phase * (180 / math.pi) * (1.2 + i * 0.08) + i * 37) * 16)
            pen = QPen(QColor(255, 45, 190, max(35, 150 - i * 11)), 2.5 if self._playing else 1.6)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2), start, int(span * 16))

        # Dense animated particle field.
        for i in range(120):
            angle = self._phase * (0.30 + (i % 11) * 0.045) + i * 0.37
            orbit_x = w * (0.18 + (i % 7) * 0.075)
            orbit_y = h * (0.13 + (i % 9) * 0.038)
            x = cx + math.sin(angle * 0.83 + i) * orbit_x
            y = cy + math.cos(angle * 1.13 + i * 0.11) * orbit_y
            radius = 1.0 + 4.0 * (0.5 + 0.5 * math.sin(angle * 2.7 + i))
            alpha = 90 + int(120 * (0.5 + 0.5 * math.sin(angle * 1.8)))
            painter.setBrush(QBrush(QColor(255, 40, 200, alpha)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x - radius), int(y - radius), int(radius * 2), int(radius * 2))

        # Central spinning energy wheel.
        spokes = 28
        spin = self._phase * (2.4 if self._playing else 0.65)
        for i in range(spokes):
            angle = spin + i * (math.pi * 2 / spokes)
            inner = 32 + 8 * math.sin(self._phase * 2.0 + i)
            outer = 105 + 28 * math.sin(self._phase * 3.0 + i * 0.61)
            x1 = cx + math.cos(angle) * inner
            y1 = cy + math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy + math.sin(angle) * outer
            alpha = 220 if self._playing else 130
            painter.setPen(QPen(QColor(255, 30, 190, alpha), 3.8 if self._playing else 2.2))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        core = 25 + int(8 * (0.5 + 0.5 * math.sin(self._phase * 3.0)))
        painter.setBrush(QBrush(QColor(255, 50, 205, 235)))
        painter.setPen(QPen(QColor(255, 220, 250, 220), 2))
        painter.drawEllipse(int(cx - core), int(cy - core), core * 2, core * 2)

        # Large upper identity marquee: ALWAYS the real liveset.
        if self._artist or self._title:
            identity = f"{self._artist or 'UNKNOWN ARTIST'}   •   {self._title or 'UNTITLED LIVESET'}   •   "
        else:
            identity = "NO LIVESET SELECTED   •   "
        painter.setFont(QFont("Arial", max(20, min(34, int(h / 13))), QFont.Weight.Black))
        painter.setPen(QPen(QColor(255, 245, 255)))
        text_width = painter.fontMetrics().horizontalAdvance(identity)
        gap = 120
        x = rect.right() - int(self._text_offset % (text_width + gap))
        y = rect.top() + 48
        painter.drawText(int(x), int(y), identity)
        painter.drawText(int(x + text_width + gap), int(y), identity)

        # Playback status and actual artist/title, large and unmistakable.
        badge = "●  NOW PLAYING" if self._playing else "○  READY TO PLAY"
        painter.setFont(QFont("Arial", max(18, min(28, int(h / 16))), QFont.Weight.Black))
        painter.setPen(QPen(QColor(255, 255, 255, 245) if self._playing else QColor(190, 190, 205)))
        painter.drawText(rect.left() + 34, rect.top() + 105, badge)

        artist = self._artist or "Select a liveset"
        title = self._title or "No liveset is currently loaded"
        artist_size = max(24, min(46, int(h / 10)))
        title_size = max(20, min(34, int(h / 14)))
        painter.setFont(QFont("Arial", artist_size, QFont.Weight.Black))
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(rect.left() + 36, rect.top() + 158, artist)
        painter.setFont(QFont("Arial", title_size, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(235, 205, 230)))
        painter.drawText(rect.left() + 38, rect.top() + 202, title)

        # Wide animated equalizer / stage floor.
        bar_count = max(60, min(150, w // 9))
        usable = w - 54
        step = usable / bar_count
        base_y = rect.bottom() - 32
        for i in range(bar_count):
            wave = (
                math.sin(self._phase * (3.8 if self._playing else 1.5) + i * 0.28)
                + 0.72 * math.sin(self._phase * (6.2 if self._playing else 2.1) - i * 0.19)
                + 0.42 * math.sin(self._phase * 1.2 + i * 0.73)
            ) / 2.14
            height = 12 + (wave + 1.0) * (h * (0.19 if self._playing else 0.12))
            x = rect.left() + 27 + i * step
            alpha = 220 if self._playing else 125
            painter.setPen(QPen(QColor(255, 35, 195, alpha), max(2.0, step * 0.50)))
            painter.drawLine(int(x), int(base_y), int(x), int(base_y - height))

        # Thin moving scanlines make the whole stage feel alive.
        for i in range(7):
            scan_y = rect.top() + ((self._text_offset * (0.45 + i * 0.07) + i * 83) % max(1, h - 4))
            painter.setPen(QPen(QColor(255, 40, 190, 18), 1))
            painter.drawLine(rect.left() + 12, int(scan_y), rect.right() - 12, int(scan_y))

        painter.end()


class LivesetDetailPage(QWidget):
    """Dedicated Liveset playback view."""

    back_requested = Signal()
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self._player = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        self.back_button = QPushButton("‹  TERUG NAAR LIVESETS")
        self.back_button.setObjectName("detailBack")
        self.back_button.clicked.connect(self.back_requested.emit)
        root.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)

        panel = QFrame()
        panel.setObjectName("detailPanel")
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(22, 22, 22, 22)
        panel_layout.setSpacing(24)

        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("detailCover")
        self.cover.setFixedSize(440, 248)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)

        self.kicker = QLabel("LIVESET")
        self.kicker.setObjectName("detailKicker")
        info.addWidget(self.kicker)

        self.title = QLabel("(geen titel)")
        self.title.setObjectName("detailTitle")
        self.title.setWordWrap(True)
        info.addWidget(self.title)

        self.artist = QLabel("")
        self.artist.setObjectName("detailArtist")
        info.addWidget(self.artist)

        self.meta = QLabel("")
        self.meta.setObjectName("detailMeta")
        self.meta.setWordWrap(True)
        info.addWidget(self.meta)
        info.addStretch(1)

        self.play_button = QPushButton("▶  PLAY LIVESET")
        self.play_button.setObjectName("detailPlay")
        self.play_button.setFixedHeight(48)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.clicked.connect(self._play)
        info.addWidget(self.play_button)

        panel_layout.addLayout(info, 1)
        root.addWidget(panel)

        self.visualizer = LivesetPlayerVisualizer()
        root.addWidget(self.visualizer, 1)

        self.setStyleSheet(paint_accent("""
            QFrame#detailPanel{background:#121217;border:1px solid #292933;border-radius:12px;}
            QLabel#detailCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:8px;}
            QLabel#detailKicker{color:#ffcf72;font-size:11px;font-weight:900;letter-spacing:1px;}
            QLabel#detailTitle{color:#fff;font-size:30px;font-weight:900;}
            QLabel#detailArtist{color:#e7e7eb;font-size:16px;font-weight:800;}
            QLabel#detailMeta{color:#858591;font-size:13px;}
            QPushButton#detailBack{background:transparent;color:#aaaab4;border:0;padding:6px 2px;font-size:12px;font-weight:800;}
            QPushButton#detailBack:hover{color:#ffcf72;}
            QPushButton#detailPlay{background:#2a1524;color:#ff4fa3;border:1px solid #5a2a48;border-radius:10px;font-size:13px;font-weight:900;}
            QPushButton#detailPlay:hover{background:#ff4fa3;color:#0e0e12;border-color:#ff4fa3;}
            QPushButton#detailPlay[playing="true"]{background:#3a1a30;color:#ff6bb5;border-color:#ff4fa3;}
        """))

    @staticmethod
    def _crop(path: str, size):
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            return QPixmap()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        return scaled.copy(x, y, size.width(), size.height())

    def bind_player(self, player):
        """Bind to the real central player and also poll it for missed signal events."""
        if self._player is player:
            return
        self._player = player
        if player is not None:
            try:
                player.play_started.connect(self.set_active_track)
            except Exception:
                pass
            try:
                player.stopped.connect(self.clear_active_track)
            except Exception:
                pass

        self._player_poll = QTimer(self)
        self._player_poll.setInterval(180)
        self._player_poll.timeout.connect(self._sync_with_player)
        self._player_poll.start()

    def _sync_with_player(self):
        if self._player is None:
            return
        path = str(getattr(self._player, "current_path", "") or "")
        playing = False
        try:
            playing = self._player.player.playbackState().name == "PlayingState"
        except Exception:
            try:
                playing = bool(path)
            except Exception:
                pass
        self._apply_active_path(path, playing)

    def _apply_active_path(self, path, playing):
        current = str(self.data.get("audio") or "").strip()
        active = str(path or "").strip()
        matches = False
        if current and active:
            try:
                matches = Path(current).resolve() == Path(active).resolve()
            except OSError:
                matches = Path(current).name.casefold() == Path(active).name.casefold()

        is_active = bool(matches and playing)
        self.play_button.setProperty("playing", is_active)
        self.play_button.setText("❚❚  PLAYING" if is_active else "▶  PLAY LIVESET")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.visualizer.set_now_playing(
            str(self.data.get("artist") or "LIVESET"),
            str(self.data.get("title") or "(geen titel)"),
            is_active,
        )

    def load_liveset(self, data):
        self.data = dict(data or {})
        self.title.setText(str(self.data.get("title") or "(geen titel)"))
        self.artist.setText(str(self.data.get("artist") or "LIVESET"))
        meta = " • ".join(
            x for x in [
                str(self.data.get("date") or ""),
                str(self.data.get("location") or ""),
                str(self.data.get("duration") or ""),
            ] if x
        )
        self.meta.setText(meta)

        pix = self._crop(str(self.data.get("cover") or ""), self.cover.size())
        if pix.isNull():
            self.cover.setPixmap(QPixmap())
            self.cover.setText("GEEN COVER")
        else:
            self.cover.setText("")
            self.cover.setPixmap(pix)

        self.play_button.setProperty("playing", False)
        self.play_button.setText("▶  PLAY LIVESET")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.visualizer.set_now_playing(
            str(self.data.get("artist") or "LIVESET"),
            str(self.data.get("title") or "(geen titel)"),
            False,
        )
        self._sync_with_player()
        self._animate_open()

    def _animate_open(self):
        self.setWindowOpacity(0.0)
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(320)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_animation = animation
        animation.start()

    def _play(self):
        path = str(self.data.get("audio") or "").strip()
        if path:
            self.play_mp3.emit(path)

    def set_active_track(self, path):
        self._apply_active_path(path, True)

    def clear_active_track(self):
        self._apply_active_path("", False)
