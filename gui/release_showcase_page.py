# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE SHOWCASE
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
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
    """Vinyl release showcase.

    The track list deliberately mirrors the CD Showcase track structure:
    position | title + artist | duration | compact play button.
    MP3 metadata is kept only as the playback source and is never rendered
    as a separate panel or long track bar.
    """

    back_requested = Signal()
    edit_requested = Signal(int)
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.release_id = None
        self._track_buttons = {}
        self._active_mp3_path = None
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
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 20)
        self.content_layout.setSpacing(16)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet("""
            QWidget { background:#0b0b0f; color:#f5f5f7; font-family:'Segoe UI Semibold'; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a;
                border-radius:7px; padding:8px 14px; font-size:12px; font-weight:800; }
            QPushButton:hover { background:#24242c; border-color:#555563; }

            /* Track rows intentionally match CD Showcase exactly. */
            QFrame#trackRow { background:#101014; border:1px solid #292933; border-radius:7px; }
            QFrame#trackRow:hover { background:#14141a; border-color:#3d3d49; }
            QLabel#trackPosition { color:#ffcf72; font-size:12px; font-weight:900; }
            QLabel#trackTitle { color:#fff; font-size:14px; font-weight:800; }
            QLabel#trackArtist { color:#8f8f9a; font-size:12px; }
            QLabel#trackDuration { color:#aaaab4; font-size:12px; }

            QPushButton#cdTrackPlayButton {
                background:#6b1717;
                color:#fff;
                border:1px solid #8f2929;
                border-radius:7px;
                padding:4px;
                font-size:15px;
                font-weight:900;
            }
            QPushButton#cdTrackPlayButton:hover {
                background:#842020;
                border-color:#b43a3a;
            }
            QPushButton#cdTrackPlayButton[playing="true"] {
                background:#1f7a3d;
                border-color:#35a65b;
            }
            QPushButton#cdTrackPlayButton[playing="true"]:hover {
                background:#29934a;
                border-color:#4fc874;
            }

            QLabel#showcaseArtist { color:#ffcf72; font-size:18px; font-weight:800; }
            QLabel#showcaseTitle { color:#fff; font-size:30px; font-weight:900; }
            QLabel#showcaseMeta { color:#9b9ba6; font-size:13px; }
            QLabel#showcaseCover {
                background:#07070a; color:#666671; border:1px solid #2a2a33; border-radius:8px;
            }
        """)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._track_buttons.clear()

    @staticmethod
    def _normalise_mp3_path(path):
        path = str(path or "").strip()
        if not path:
            return ""
        try:
            return str(Path(path).expanduser().resolve()).casefold()
        except OSError:
            return path.casefold()

    @staticmethod
    def _format_duration(duration):
        if duration in (None, ""):
            return ""
        try:
            seconds = int(duration)
            return f"{seconds // 60}:{seconds % 60:02d}"
        except (ValueError, TypeError):
            return str(duration)

    def _set_play_button_active(self, button, active):
        if button is None:
            return
        button.setProperty("playing", bool(active))
        button.setText("❚❚" if active else "▶")
        style = button.style()
        style.unpolish(button)
        style.polish(button)
        button.update()

    def _set_active_mp3_path(self, path):
        normalised = self._normalise_mp3_path(path)
        self._active_mp3_path = normalised or None
        for button_path, button in self._track_buttons.items():
            self._set_play_button_active(
                button,
                bool(normalised) and button_path == normalised,
            )

    def set_active_track(self, path):
        self._set_active_mp3_path(path)

    def clear_active_track(self):
        self._set_active_mp3_path("")

    def set_playback_state(self, state):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            is_playing = state == QMediaPlayer.PlaybackState.PlayingState
        except Exception:
            is_playing = False
        if is_playing:
            self._set_active_mp3_path(self._active_mp3_path or "")
        else:
            self.clear_active_track()

    def _make_track_row(self, track, release_artist):
        """Create the compact Vinyl row using the CD Showcase geometry."""
        row = QFrame()
        row.setObjectName("trackRow")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(12)

        position = QLabel(str(track[1] or ""))
        position.setObjectName("trackPosition")
        position.setFixedWidth(52)
        layout.addWidget(position)

        middle = QVBoxLayout()
        middle.setSpacing(2)

        title = QLabel(str(track[3] or "(geen titel)"))
        title.setObjectName("trackTitle")
        title.setWordWrap(True)
        middle.addWidget(title)

        artist = str(track[2] or release_artist or "").strip()
        if artist:
            artist_label = QLabel(artist)
            artist_label.setObjectName("trackArtist")
            artist_label.setWordWrap(True)
            middle.addWidget(artist_label)

        layout.addLayout(middle, 1)

        duration = QLabel(self._format_duration(track[4]))
        duration.setObjectName("trackDuration")
        duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duration.setFixedWidth(55)
        layout.addWidget(duration)

        mp3_path = str(track[7] or "").strip()
        if mp3_path:
            play_button = QPushButton("▶")
            play_button.setObjectName("cdTrackPlayButton")
            play_button.setProperty("playing", False)
            play_button.setProperty("mp3_path", mp3_path)
            play_button.setToolTip(f"Speel MP3: {Path(mp3_path).name}")
            play_button.setFixedSize(38, 32)
            play_button.setCursor(Qt.CursorShape.PointingHandCursor)
            play_button.setEnabled(Path(mp3_path).exists())
            button_path = self._normalise_mp3_path(mp3_path)
            self._track_buttons[button_path] = play_button
            self._set_play_button_active(
                play_button,
                button_path == self._active_mp3_path,
            )
            play_button.clicked.connect(
                lambda _checked=False, path=mp3_path: self.play_mp3.emit(path)
            )
            layout.addWidget(play_button)
        else:
            no_mp3 = QLabel("GEEN MP3")
            no_mp3.setObjectName("trackArtist")
            no_mp3.setFixedWidth(62)
            no_mp3.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(no_mp3)

        return row

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
                SELECT
                    t.id,
                    t.position,
                    t.artist,
                    t.title,
                    t.duration,
                    t.bpm,
                    (
                        SELECT m.path
                        FROM track_mp3 tm
                        JOIN mp3_files m ON m.id = tm.mp3_id
                        WHERE tm.track_id = t.id
                        ORDER BY tm.is_preferred DESC, tm.id
                        LIMIT 1
                    ) AS mp3_path,
                    t.release_id
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

        artist = str(release[1] or "Onbekend")
        title = str(release[2] or "(geen titel)")
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
                cover.setPixmap(
                    pix.scaled(
                        320,
                        320,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        hero_layout.addWidget(cover)

        info = QVBoxLayout()
        info.setSpacing(8)

        artist_label = QLabel(artist)
        artist_label.setObjectName("showcaseArtist")
        info.addWidget(artist_label)

        title_label = QLabel(title)
        title_label.setObjectName("showcaseTitle")
        title_label.setWordWrap(True)
        info.addWidget(title_label)

        meta = []
        for value in (release[3], release[4], release[5], release[6]):
            if value:
                meta.append(str(value))
        if release[11]:
            meta.append(f"KAST: {release[11]}")
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
                discogs_button.clicked.connect(
                    lambda _checked=False, url=discogs_url: QDesktopServices.openUrl(QUrl(url))
                )
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
            self.content_layout.addWidget(self._make_track_row(track, artist))

        self.content_layout.addStretch()

    def _edit(self):
        if self.release_id is not None:
            self.edit_requested.emit(self.release_id)
