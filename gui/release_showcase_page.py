# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE SHOWCASE
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)

from database.database import get_connection


class ReleaseShowcasePage(QWidget):

    back_requested = Signal()
    edit_requested = Signal(int)
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.release_id = None
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        self.back_button = QPushButton("← TERUG NAAR BOARD")
        self.back_button.clicked.connect(self.back_requested.emit)
        top.addWidget(self.back_button)
        top.addStretch()

        self.edit_button = QPushButton("BEWERKEN")
        self.edit_button.clicked.connect(self._edit)
        top.addWidget(self.edit_button)
        root.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 20)
        self.content_layout.setSpacing(16)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet("""
            QWidget { background: #0b0b0f; color: #f5f5f7; font-family: 'Segoe UI Semibold'; }
            QPushButton {
                background: #18181f; color: #fff; border: 1px solid #30303a;
                border-radius: 7px; padding: 8px 14px; font-size: 12px; font-weight: 800;
            }
            QPushButton:hover { background: #24242c; border-color: #555563; }
            QPushButton#showcasePlay {
                background: #6b1717; color: #fff; border-color: #8f2929;
                border-radius: 7px; min-width: 82px; min-height: 34px;
                font-size: 12px; font-weight: 900;
            }
            QPushButton#showcasePlay:hover { background: #842020; border-color: #b43a3a; }
            QPushButton#showcasePlay[playing="true"] {
                background: #218c4a; color: #fff; border-color: #39b866;
            }
            QPushButton#showcasePlay[playing="true"]:hover { background: #2aa65a; border-color: #51d77c; }
            QLabel#showcaseArtist { color: #ffcf72; font-size: 18px; font-weight: 800; }
            QLabel#showcaseTitle { color: #fff; font-size: 30px; font-weight: 900; }
            QLabel#showcaseMeta { color: #9b9ba6; font-size: 13px; }
            QLabel#showcaseCover {
                background: #07070a; color: #666671; border: 1px solid #2a2a33; border-radius: 8px;
            }
            QFrame#showcaseCard {
                background: #121217; border: 1px solid #292933; border-radius: 10px;
            }
            QFrame#showcaseCard:hover { background: #17171e; border-color: #3d3d49; }
            QLabel#trackPosition { color: #ffcf72; font-size: 13px; font-weight: 900; }
            QLabel#trackTitle { color: #fff; font-size: 15px; font-weight: 800; }
            QLabel#trackMeta { color: #858591; font-size: 11px; }
            QLabel#trackStatus { color: #55d982; font-size: 10px; font-weight: 900; }
        """)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_release(self, release_id):
        self.release_id = int(release_id)
        self._clear()

        conn = get_connection()
        try:
            release = conn.execute(
                """
                SELECT id, artist, title, label, catalog, year, genre,
                       discogs, discogs_link, cover, notes, storage_code, checked
                FROM releases WHERE id = ?
                """,
                (self.release_id,),
            ).fetchone()

            tracks = conn.execute(
                """
                SELECT t.id, t.position, t.title, t.duration, t.bpm,
                       (
                           SELECT m.path
                           FROM track_mp3 tm
                           JOIN mp3_files m ON m.id = tm.mp3_id
                           WHERE tm.track_id = t.id
                           ORDER BY tm.is_preferred DESC, tm.id
                           LIMIT 1
                       ) AS mp3_path
                FROM tracks t
                WHERE t.release_id = ?
                ORDER BY t.id
                """,
                (self.release_id,),
            ).fetchall()
        finally:
            conn.close()

        if release is None:
            self.content_layout.addWidget(QLabel("Release niet gevonden"))
            return

        artist, title = str(release[1] or "Onbekend"), str(release[2] or "(geen titel)")
        cover_path = str(release[9] or "").strip()

        hero = QFrame()
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(22)

        cover = QLabel("GEEN COVER")
        cover.setObjectName("showcaseCover")
        cover.setFixedSize(320, 320)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if cover_path and Path(cover_path).exists():
            pix = QPixmap(cover_path)
            if not pix.isNull():
                cover.setPixmap(pix.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hero_layout.addWidget(cover)

        info = QVBoxLayout()
        info.setSpacing(8)
        artist_label = QLabel(artist)
        artist_label.setObjectName("showcaseArtist")
        title_label = QLabel(title)
        title_label.setObjectName("showcaseTitle")
        title_label.setWordWrap(True)
        info.addWidget(artist_label)
        info.addWidget(title_label)

        meta = []
        if release[3]: meta.append(str(release[3]))
        if release[4]: meta.append(str(release[4]))
        if release[5]: meta.append(str(release[5]))
        if release[6]: meta.append(str(release[6]))
        if release[11]: meta.append(f"KAST: {release[11]}")
        meta_label = QLabel(" • ".join(meta))
        meta_label.setObjectName("showcaseMeta")
        meta_label.setWordWrap(True)
        info.addWidget(meta_label)

        if release[7]:
            discogs_label = QLabel(f"Discogs: {release[7]}")
            discogs_label.setObjectName("showcaseMeta")
            info.addWidget(discogs_label)
            if release[8]:
                discogs_button = QPushButton("OPEN DISCOGS")
                discogs_url = str(release[8])
                discogs_button.clicked.connect(lambda _checked=False, url=discogs_url: QDesktopServices.openUrl(QUrl(url)))
                info.addWidget(discogs_button, 0, Qt.AlignmentFlag.AlignLeft)

        if release[10]:
            notes = QLabel(str(release[10]))
            notes.setObjectName("showcaseMeta")
            notes.setWordWrap(True)
            info.addSpacing(12)
            info.addWidget(notes)

        info.addStretch()
        hero_layout.addLayout(info, 1)
        self.content_layout.addWidget(hero)

        tracks_title = QLabel(f"TRACKS  •  {len(tracks)}")
        tracks_title.setObjectName("showcaseArtist")
        self.content_layout.addWidget(tracks_title)

        for track in tracks:
            track_id, position, track_title, duration, bpm, mp3_path = track
            card = QFrame()
            card.setObjectName("showcaseCard")
            row = QHBoxLayout(card)
            row.setContentsMargins(14, 10, 14, 10)
            row.setSpacing(12)

            pos = QLabel(str(position or ""))
            pos.setObjectName("trackPosition")
            pos.setFixedWidth(48)
            row.addWidget(pos)

            text = QVBoxLayout()
            text.setSpacing(3)
            name = QLabel(str(track_title or "(geen titel)"))
            name.setObjectName("trackTitle")
            name.setWordWrap(True)
            text.addWidget(name)

            details = []
            if duration:
                try:
                    seconds = int(duration)
                    details.append(f"{seconds // 60}:{seconds % 60:02d}")
                except (ValueError, TypeError):
                    pass
            if bpm:
                try:
                    details.append(f"{float(bpm):.1f} BPM")
                except (ValueError, TypeError):
                    pass
            meta_track = QLabel(" • ".join(details) if details else "Geen MP3-info")
            meta_track.setObjectName("trackMeta")
            text.addWidget(meta_track)
            row.addLayout(text, 1)

            path = str(mp3_path or "").strip()
            play = QPushButton("▶ PLAY")
            play.setObjectName("showcasePlay")
            play.setEnabled(bool(path) and Path(path).exists())
            play.setCursor(Qt.CursorShape.PointingHandCursor)
            if path:
                play.clicked.connect(lambda checked=False, p=path: self.play_mp3.emit(p))
            row.addWidget(play)
            self.content_layout.addWidget(card)

        self.content_layout.addStretch()

    def set_active_track(self, path):
        """Update all currently displayed Vinyl track buttons to the shared red/green state."""
        active = str(path or "").casefold()
        for index in range(self.content_layout.count()):
            item = self.content_layout.itemAt(index)
            card = item.widget()
            if not isinstance(card, QFrame) or card.objectName() != "showcaseCard":
                continue
            buttons = card.findChildren(QPushButton, "showcasePlay")
            if not buttons:
                continue
            button = buttons[0]
            # The emitted path is stored on the button so state survives refresh-free playback updates.
            button_path = str(button.property("mp3_path") or "").casefold()
            playing = bool(active and button_path and Path(active).name == Path(button_path).name)
            button.setProperty("playing", playing)
            button.setText("❚❚ PLAYING" if playing else "▶ PLAY")
            button.style().unpolish(button)
            button.style().polish(button)

    def clear_active_track(self):
        self.set_active_track("")

    def _edit(self):
        if self.release_id is not None:
            self.edit_requested.emit(self.release_id)
