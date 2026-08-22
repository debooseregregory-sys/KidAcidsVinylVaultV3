from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu

from database.database import set_preferred_mp3
from gui.mp3_search_dialog import MP3SearchDialog
from gui.release_detail_page import TrackEditDialog


class CompactTrackCard(QFrame):
    """Compact Vinyl track row matching the CD Showcase structure."""

    play_mp3 = Signal(str)
    unlink_mp3_requested = Signal(int)
    mp3_linked = Signal()
    track_changed = Signal()

    def __init__(self, track_data, parent=None):
        super().__init__(parent)
        self.track = track_data["track"]
        self.mp3s = track_data["mp3s"]
        self._play_button = None
        self._active = False
        self._build()

    @staticmethod
    def _duration(value):
        if value in (None, ""):
            return ""
        try:
            seconds = int(value)
            return f"{seconds // 60}:{seconds % 60:02d}"
        except (TypeError, ValueError):
            return str(value)

    def _preferred_mp3(self):
        if not self.mp3s:
            return None
        for mp3 in self.mp3s:
            if mp3.get("is_preferred"):
                return mp3
        return self.mp3s[0]

    def _set_playing(self, active):
        self._active = bool(active)
        if self._play_button is None:
            return
        self._play_button.setProperty("playing", self._active)
        style = self._play_button.style()
        style.unpolish(self._play_button)
        style.polish(self._play_button)
        self._play_button.update()

    def _build(self):
        self.setObjectName("trackRow")
        self.setStyleSheet("""
            QFrame#trackRow {
                background:#101014;
                border:1px solid #292933;
                border-radius:7px;
            }
            QLabel#trackPosition { color:#ffcf72; font-size:12px; font-weight:900; }
            QLabel#trackTitle { color:#fff; font-size:14px; font-weight:800; }
            QLabel#trackArtist { color:#8f8f9a; font-size:12px; }
            QLabel#trackDuration { color:#aaaab4; font-size:12px; }
            QPushButton#cdTrackPlayButton {
                background:#6b1717; color:#fff; border:1px solid #8f2929;
                border-radius:7px; padding:4px; font-size:15px; font-weight:900;
            }
            QPushButton#cdTrackPlayButton:hover {
                background:#842020; border-color:#b43a3a;
            }
            QPushButton#cdTrackPlayButton[playing="true"] {
                background:#1f7a3d; border-color:#35a65b;
            }
            QPushButton#cdTrackPlayButton[playing="true"]:hover {
                background:#29934a; border-color:#4fc874;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(12)

        position = QLabel(str(self.track.get("position") or ""))
        position.setObjectName("trackPosition")
        position.setFixedWidth(52)
        layout.addWidget(position)

        middle = QVBoxLayout()
        middle.setSpacing(2)

        title = QLabel(str(self.track.get("title") or "(geen titel)"))
        title.setObjectName("trackTitle")
        title.setWordWrap(True)
        middle.addWidget(title)

        artist = QLabel(str(self.track.get("artist") or ""))
        artist.setObjectName("trackArtist")
        artist.setWordWrap(True)
        if artist.text():
            middle.addWidget(artist)

        layout.addLayout(middle, 1)

        duration = QLabel(self._duration(self.track.get("duration")))
        duration.setObjectName("trackDuration")
        duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duration.setFixedWidth(55)
        layout.addWidget(duration)

        mp3 = self._preferred_mp3()
        if mp3 and mp3.get("path"):
            path = str(mp3["path"]).strip()
            button = QPushButton("▶")
            button.setObjectName("cdTrackPlayButton")
            button.setProperty("playing", False)
            button.setFixedSize(38, 32)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip(f"Speel MP3: {Path(path).name}")
            button.clicked.connect(lambda _=False, p=path: self._play(p))
            self._play_button = button
            layout.addWidget(button)
        else:
            no_mp3 = QLabel("GEEN MP3")
            no_mp3.setObjectName("trackArtist")
            no_mp3.setFixedWidth(62)
            no_mp3.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(no_mp3)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def _play(self, path):
        self._set_playing(True)
        self.play_mp3.emit(path)

    def mouseDoubleClickEvent(self, event):
        self.edit_track()
        super().mouseDoubleClickEvent(event)

    def _context_menu(self, position):
        menu = QMenu(self)
        edit = menu.addAction("Track bewerken")
        delete = menu.addAction("Track verwijderen")
        menu.addSeparator()
        search = menu.addAction("MP3 koppelen")

        preferred = {}
        unlink = {}
        for mp3 in self.mp3s:
            link_id = mp3.get("link_id")
            if link_id is None:
                continue
            name = str(mp3.get("filename") or mp3.get("path") or "MP3")
            preferred[menu.addAction(f"Voorkeur: {name}")] = link_id
            unlink[menu.addAction(f"Ontkoppel: {name}")] = link_id

        chosen = menu.exec(self.mapToGlobal(position))
        if chosen is edit:
            self.edit_track()
        elif chosen is delete:
            self.delete_track()
        elif chosen is search:
            self.open_mp3_search()
        elif chosen in preferred:
            self.set_preferred_mp3(preferred[chosen])
        elif chosen in unlink:
            self.unlink_mp3_requested.emit(unlink[chosen])

    def edit_track(self):
        dialog = TrackEditDialog(self.track, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        data = dialog.result_data
        from database.database import get_connection
        connection = get_connection()
        try:
            connection.execute("""
                UPDATE tracks SET position=?, artist=?, title=?, duration=?, bpm=?, genre=?, notes=?
                WHERE id=?
            """, (data["position"], data["artist"], data["title"], data["duration"], data["bpm"], data["genre"], data["notes"], self.track["id"]))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        self.track_changed.emit()

    def delete_track(self):
        from PySide6.QtWidgets import QMessageBox
        answer = QMessageBox.question(self, "Track verwijderen", "Deze track verwijderen? De MP3-koppelingen worden ook verwijderd.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        from database.database import get_connection
        connection = get_connection()
        try:
            connection.execute("DELETE FROM track_mp3 WHERE track_id=?", (self.track["id"],))
            connection.execute("DELETE FROM tracks WHERE id=?", (self.track["id"],))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        self.track_changed.emit()

    def open_mp3_search(self):
        dialog = MP3SearchDialog(self.track, self)
        dialog.mp3_selected.connect(self.link_selected_mp3)
        dialog.exec()

    def link_selected_mp3(self, mp3_id, path):
        from database.database import get_connection
        connection = get_connection()
        try:
            existing = connection.execute("SELECT id FROM track_mp3 WHERE track_id=? AND mp3_id=?", (self.track["id"], mp3_id)).fetchone()
            if existing:
                return
            preferred_exists = connection.execute("SELECT id FROM track_mp3 WHERE track_id=? AND is_preferred=1 LIMIT 1", (self.track["id"],)).fetchone()
            connection.execute("""
                INSERT INTO track_mp3 (track_id, mp3_id, score, is_preferred, manually_added)
                VALUES (?, ?, ?, ?, ?)
            """, (self.track["id"], mp3_id, 100.0, 0 if preferred_exists else 1, 1))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        self.mp3_linked.emit()

    def set_preferred_mp3(self, link_id):
        set_preferred_mp3(self.track["id"], link_id)
        self.mp3_linked.emit()
