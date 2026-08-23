from __future__ import annotations

from gui.app_settings import paint_accent

import math
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QFont, QLinearGradient
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class LivesetPlayerVisualizer(QWidget):
    """Large animated visual for the actual liveset playback page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(330)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._phase = 0.0
        self._text_offset = 0.0
        self._artist = ""
        self._title = ""
        self._playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(24)

    def set_liveset(self, artist, title, playing=False):
        self._artist = str(artist or "").strip()
        self._title = str(title or "").strip()
        self._playing = bool(playing)
        self.update()

    def set_now_playing(self, artist, title):
        self._artist = str(artist or "").strip()
        self._title = str(title or "").strip()
        self._playing = True
        self.update()

    def set_playing(self, playing):
        self._playing = bool(playing)
        self.update()

    def _animate(self):
        self._phase = (self._phase + 0.045) % (math.pi * 2)
        self._text_offset = (self._text_offset + 2.2) % 2000
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        w, h = rect.width(), rect.height()
        cx, cy = rect.center().x(), rect.top() + h * 0.43

        bg = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        bg.setColorAt(0.0, Qt.GlobalColor.black)
        bg.setColorAt(0.45, Qt.GlobalColor.darkMagenta)
        bg.setColorAt(1.0, Qt.GlobalColor.black)
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(Qt.GlobalColor.darkMagenta, 1.5))
        painter.drawRoundedRect(rect, 18, 18)

        pulse = 35 + 22 * (0.5 + 0.5 * math.sin(self._phase * 2.0))
        for ring in range(7):
            radius = pulse + ring * 30
            painter.setPen(QPen(Qt.GlobalColor.magenta, max(1.0, 3.2 - ring * 0.35)))
            painter.setBrush(QBrush(Qt.GlobalColor.transparent))
            painter.drawEllipse(int(cx - radius), int(cy - radius), int(radius * 2), int(radius * 2))

        for i in range(70):
            angle = self._phase * (0.32 + (i % 8) * 0.055) + i * 0.39
            orbit_x = w * (0.18 + (i % 5) * 0.09)
            orbit_y = h * (0.16 + (i % 7) * 0.045)
            x = cx + math.sin(angle * 0.83 + i) * orbit_x
            y = cy + math.cos(angle * 1.11 + i * 0.17) * orbit_y
            radius = 1.2 + 3.2 * (0.5 + 0.5 * math.sin(angle * 2.1))
            painter.setBrush(QBrush(Qt.GlobalColor.magenta))
            painter.setPen(QPen(Qt.GlobalColor.magenta, 1))
            painter.drawEllipse(int(x - radius), int(y - radius), int(radius * 2), int(radius * 2))

        for i in range(16):
            angle = self._phase * 1.7 + i * (math.pi * 2 / 16)
            inner = 20 + 4 * math.sin(self._phase * 2)
            outer = 66 + 15 * math.sin(self._phase * 3 + i * 0.7)
            x1 = cx + math.cos(angle) * inner
            y1 = cy + math.sin(angle) * inner
            x2 = cx + math.cos(angle) * outer
            y2 = cy + math.sin(angle) * outer
            painter.setPen(QPen(Qt.GlobalColor.magenta, 3.0))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.setBrush(QBrush(Qt.GlobalColor.magenta))
        painter.setPen(QPen(Qt.GlobalColor.lightGray, 2))
        painter.drawEllipse(int(cx - 13), int(cy - 13), 26, 26)

        bar_count = max(48, min(110, w // 13))
        usable = w - 50
        step = usable / bar_count
        base_y = rect.bottom() - 42
        for i in range(bar_count):
            wave = (
                math.sin(self._phase * 2.7 + i * 0.31)
                + 0.72 * math.sin(self._phase * 4.6 - i * 0.17)
                + 0.38 * math.sin(self._phase * 1.35 + i * 0.77)
            ) / 2.1
            height = 12 + (wave + 1.0) * (h * 0.13)
            x = rect.left() + 25 + i * step
            painter.setPen(QPen(Qt.GlobalColor.magenta, max(2.0, step * 0.42)))
            painter.drawLine(int(x), int(base_y), int(x), int(base_y - height))

        text = "KID ACID  •  LIVESET  •  ACID HOUSE  •  TECHNO  •  DEEP GROOVES  •  "
        painter.setFont(QFont("Arial", max(12, min(18, int(h / 25))), QFont.Weight.Bold))
        painter.setPen(QPen(Qt.GlobalColor.lightGray))
        text_width = painter.fontMetrics().horizontalAdvance(text)
        x = rect.right() - int(self._text_offset % (text_width + 80))
        y = rect.top() + 32
        painter.drawText(int(x), int(y), text)
        painter.drawText(int(x + text_width + 80), int(y), text)

        status = "NOW PLAYING" if self._playing else "READY TO PLAY"
        painter.setFont(QFont("Arial", max(16, min(28, int(h / 14))), QFont.Weight.Black))
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(rect.left() + 26, rect.top() + 82, status)

        identity = " • ".join(x for x in (self._artist, self._title) if x)
        if not identity:
            identity = "LIVESET"
        painter.setFont(QFont("Arial", max(18, min(34, int(h / 12))), QFont.Weight.Bold))
        painter.drawText(rect.left() + 28, rect.top() + 126, identity)
        painter.end()


class LivesetDetailPage(QWidget):
    """Dedicated Liveset playback view."""

    back_requested = Signal()
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self._player = None
        self._last_active_path = ""
        self._build()
        self._player_sync_timer = QTimer(self)
        self._player_sync_timer.setInterval(150)
        self._player_sync_timer.timeout.connect(self._sync_from_central_player)
        self._player_sync_timer.start()

    def bind_player(self, player):
        self._player = player
        self._sync_from_central_player()

    @staticmethod
    def _same_path(left, right):
        if not left or not right:
            return False
        try:
            return Path(left).resolve() == Path(right).resolve()
        except (OSError, RuntimeError):
            return str(left).lower() == str(right).lower()

    @staticmethod
    def _identity_from_audio(path: str):
        """Get the identity from the file that is actually playing.

        The central player's current_path is authoritative. This prevents a
        stale/incorrect Library artist or title from being shown as NOW PLAYING.
        """
        name = Path(str(path or "")).stem.strip()
        if not name:
            return "", ""
        if " - " in name:
            artist, title = name.split(" - ", 1)
            return artist.strip(), title.strip()
        return "", name

    def _sync_from_central_player(self):
        player = self._player
        if player is None or not self.data:
            return
        try:
            path = str(getattr(player, "current_path", None) or "").strip()
            state = player.player.playbackState()
            playing = state == player.player.PlaybackState.PlayingState
        except Exception:
            return

        active = str(self.data.get("audio") or "").strip()
        same_file = bool(path and active and self._same_path(path, active))

        if same_file and playing:
            fallback_artist, fallback_title = self._identity_from_audio(path)
            # IMPORTANT: the actual playing filename wins over Library metadata.
            artist = fallback_artist or str(self.data.get("artist") or "").strip()
            title = fallback_title or str(self.data.get("title") or "").strip()

            if path != self._last_active_path:
                self._last_active_path = path

            self.visualizer.set_now_playing(artist, title)
            self.play_button.setProperty("playing", True)
            self.play_button.setText("❚❚  PLAYING")
        else:
            self._last_active_path = ""
            self.visualizer.set_playing(False)
            self.play_button.setProperty("playing", False)
            self.play_button.setText("▶  PLAY LIVESET")

        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)

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
        scaled = pix.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        return scaled.copy(x, y, size.width(), size.height())

    def load_liveset(self, data):
        self.data = dict(data or {})
        self._last_active_path = ""
        audio_path = str(self.data.get("audio") or "").strip()
        fallback_artist, fallback_title = self._identity_from_audio(audio_path)
        artist = str(self.data.get("artist") or "").strip() or fallback_artist
        title = str(self.data.get("title") or "").strip() or fallback_title

        self.title.setText(title or "(geen titel)")
        self.artist.setText(artist or "LIVESET")
        meta = " • ".join(
            x for x in (
                str(self.data.get("date") or ""),
                str(self.data.get("location") or ""),
                str(self.data.get("duration") or ""),
            ) if x
        )
        self.meta.setText(meta)

        pix = self._crop(str(self.data.get("cover") or ""), self.cover.size())
        if pix.isNull():
            self.cover.setPixmap(QPixmap())
            self.cover.setText("GEEN COVER")
        else:
            self.cover.setText("")
            self.cover.setPixmap(pix)

        self.visualizer.set_liveset(artist, title, False)
        self.play_button.setProperty("playing", False)
        self.play_button.setText("▶  PLAY LIVESET")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self._animate_open()
        self._sync_from_central_player()

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
        self._sync_from_central_player()

    def clear_active_track(self):
        self._last_active_path = ""
        self._sync_from_central_player()
