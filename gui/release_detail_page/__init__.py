"""
Kid Acid's VinylVault V3
Compact Vinyl track presentation adapter.

This package intentionally shadows the legacy gui/release_detail_page.py
module while loading that complete implementation underneath.  Only the
visual TrackCard is replaced.  The existing ReleaseDetailPage, dialogs,
MP3 linking, preferred-MP3 handling, unlinking and database behaviour remain
available from the original implementation.
"""

from pathlib import Path
import importlib.util
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMenu


# ---------------------------------------------------------------------------
# Load the original implementation under a private module name.
# ---------------------------------------------------------------------------

_original_path = Path(__file__).resolve().parent.parent / "release_detail_page.py"
_original_spec = importlib.util.spec_from_file_location(
    "gui._legacy_release_detail_page",
    _original_path,
)

if _original_spec is None or _original_spec.loader is None:
    raise ImportError(f"Kan legacy release_detail_page niet laden: {_original_path}")

_legacy = importlib.util.module_from_spec(_original_spec)
_original_spec.loader.exec_module(_legacy)


class CompactTrackCard(_legacy.TrackCard):
    """Compact Vinyl track row matching the CD Showcase structure."""

    def build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("vinylCompactTrackRow")
        self.setMinimumHeight(48)
        self.setMaximumHeight(56)

        self.setStyleSheet(
            """
            QFrame#vinylCompactTrackRow {
                background-color: #171717;
                border: 1px solid #352d46;
                border-radius: 7px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QLabel#vinylTrackPosition {
                color: #d84b91;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#vinylTrackTitle {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#vinylTrackArtist {
                color: #aaaaaa;
                font-size: 11px;
            }
            QLabel#vinylTrackDuration {
                color: #9688aa;
                font-size: 12px;
            }
            QPushButton#vinylTrackPlayButton {
                background-color: #5a1717;
                color: #ffffff;
                border: 1px solid #7a2525;
                border-radius: 5px;
                padding: 0px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#vinylTrackPlayButton:hover {
                background-color: #702020;
                border: 1px solid #a53a3a;
            }
            QPushButton#vinylTrackPlayButton[playing="true"] {
                background-color: #287a3c;
                border: 1px solid #3ca957;
            }
            QLabel#vinylNoMp3 {
                color: #6f6878;
                font-size: 11px;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        position = QLabel(str(self.track["position"] or ""))
        position.setObjectName("vinylTrackPosition")
        position.setFixedWidth(52)
        layout.addWidget(position)

        middle = QVBoxLayout()
        middle.setSpacing(0)
        middle.setContentsMargins(0, 0, 0, 0)

        title = QLabel(str(self.track["title"] or "(geen titel)"))
        title.setObjectName("vinylTrackTitle")
        title.setWordWrap(False)
        middle.addWidget(title)

        artist = str(self.track["artist"] or "").strip()
        if artist:
            artist_label = QLabel(artist)
            artist_label.setObjectName("vinylTrackArtist")
            artist_label.setWordWrap(False)
            middle.addWidget(artist_label)

        layout.addLayout(middle, 1)

        duration_value = self.track["duration"]
        duration_text = ""
        try:
            if duration_value is not None and str(duration_value).strip():
                seconds = int(float(duration_value))
                duration_text = f"{seconds // 60}:{seconds % 60:02d}"
        except (TypeError, ValueError):
            duration_text = str(duration_value or "")

        duration = QLabel(duration_text)
        duration.setObjectName("vinylTrackDuration")
        duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duration.setFixedWidth(55)
        layout.addWidget(duration)

        self._active_mp3_path = None
        self._play_button = None

        preferred = None
        if self.mp3s:
            preferred = next(
                (mp3 for mp3 in self.mp3s if mp3["is_preferred"]),
                self.mp3s[0],
            )

        mp3_path = str((preferred or {}).get("path") or "").strip() if preferred else ""

        if mp3_path:
            button = QPushButton("▶")
            button.setObjectName("vinylTrackPlayButton")
            button.setProperty("playing", False)
            button.setFixedSize(38, 32)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip("Speel track")
            button.clicked.connect(
                lambda _checked=False, path=mp3_path: self._play_compact(path)
            )
            layout.addWidget(button)
            self._play_button = button
        else:
            no_mp3 = QLabel("GEEN MP3")
            no_mp3.setObjectName("vinylNoMp3")
            no_mp3.setFixedWidth(62)
            no_mp3.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_mp3)

    def _play_compact(self, path):
        self.set_active_track(path)
        self.play_mp3.emit(path)

    @staticmethod
    def _normalise_path(path):
        path = str(path or "").strip()
        if not path:
            return ""
        try:
            return str(Path(path).expanduser().resolve()).casefold()
        except OSError:
            return path.casefold()

    def set_active_track(self, path):
        self._active_mp3_path = self._normalise_path(path) or None
        if self._play_button is not None:
            self._play_button.setProperty(
                "playing",
                bool(self._active_mp3_path),
            )
            style = self._play_button.style()
            style.unpolish(self._play_button)
            style.polish(self._play_button)
            self._play_button.update()

    def clear_active_track(self):
        self._active_mp3_path = None
        if self._play_button is not None:
            self._play_button.setProperty("playing", False)
            style = self._play_button.style()
            style.unpolish(self._play_button)
            style.polish(self._play_button)
            self._play_button.update()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        edit_action = menu.addAction("Track bewerken")
        search_action = menu.addAction("MP3 koppelen / zoeken")
        menu.addSeparator()
        delete_action = menu.addAction("Track verwijderen")

        chosen = menu.exec(event.globalPos())
        if chosen is edit_action:
            self.edit_track()
        elif chosen is search_action:
            self.open_mp3_search()
        elif chosen is delete_action:
            self.delete_track()


# Make the complete legacy page use the compact card without touching its
# database/editor/MP3-linking implementation.
_legacy.TrackCard = CompactTrackCard


# Re-export the original public page and supporting classes.
TrackCard = CompactTrackCard
ReleaseDetailPage = _legacy.ReleaseDetailPage
TrackEditDialog = _legacy.TrackEditDialog
SideHeader = _legacy.SideHeader

__all__ = [
    "ReleaseDetailPage",
    "TrackCard",
    "CompactTrackCard",
    "TrackEditDialog",
    "SideHeader",
]
