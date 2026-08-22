# ============================================================
# KID ACID'S VINYLVAULT V3
# LIVESETS SHOWCASE
# ============================================================

"""Livesets section matching the existing CD Showcase visual language.

VinylVault V3 is a native PySide6 desktop application, so this page uses
Qt widgets instead of introducing a separate React/Tailwind frontend.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QMimeData, QPropertyAnimation, QTimer, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"
LIVESETS_COVERS = DATA_DIR / "liveset_covers"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class CoverDropZone(QFrame):
    """Click/drag-and-drop cover picker used by the liveset editor."""

    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("coverDropZone")
        self.setMinimumHeight(150)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)

        self.icon = QLabel("＋")
        self.icon.setObjectName("uploadIcon")
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon)

        title = QLabel("Upload cover")
        title.setObjectName("uploadTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("Sleep een afbeelding hierheen of klik om te kiezen")
        hint.setObjectName("uploadHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Kies cover",
                "",
                "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)",
            )
            if path:
                self.file_selected.emit(path)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self._has_image(event.mimeData()):
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self._polish()
            self.icon.setText("✦")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self._polish()
        self.icon.setText("＋")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and Path(path).suffix.lower() in IMAGE_EXTENSIONS:
                self.file_selected.emit(path)
                break
        self.setProperty("dragging", False)
        self._polish()
        self.icon.setText("＋")
        event.acceptProposedAction()

    def _polish(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    @staticmethod
    def _has_image(mime: QMimeData) -> bool:
        return any(
            Path(url.toLocalFile()).suffix.lower() in IMAGE_EXTENSIONS
            for url in mime.urls()
        )


class LiveSetCard(QFrame):
    """Liveset card deliberately follows CD Showcase card proportions."""

    play_requested = Signal(str)
    cover_requested = Signal(str)

    def __init__(self, data: dict, delay_ms: int = 0, parent=None):
        super().__init__(parent)
        self.data = data
        self._playing = False
        self._fade = None
        self._cover_pixmap = QPixmap()
        self._build()
        QTimer.singleShot(delay_ms, self._fade_in)

    def _build(self):
        self.setObjectName("releaseCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(230)
        self.setMaximumWidth(340)
        self.setMinimumHeight(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 12)
        root.setSpacing(7)

        # 16:9 cover, larger than the CD Showcase card while keeping all
        # information immediately below the image. The pixmap is center-cropped.
        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("cover")
        self.cover.setFixedHeight(185)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(False)
        root.addWidget(self.cover)

        self._load_cover(self.data.get("cover", ""))

        artist = QLabel(str(self.data.get("artist") or self.data.get("location") or "LIVESET"))
        artist.setObjectName("artist")
        artist.setWordWrap(True)
        root.addWidget(artist)

        title = QLabel(str(self.data.get("title") or "(geen titel)"))
        title.setObjectName("title")
        title.setWordWrap(True)
        root.addWidget(title)

        meta_parts = [
            str(self.data.get("date") or "").strip(),
            str(self.data.get("location") or "").strip(),
        ]
        meta = QLabel(" • ".join(part for part in meta_parts if part))
        meta.setObjectName("meta")
        meta.setWordWrap(True)
        if not meta.text():
            meta.setText("Geen datum / locatie")
        root.addWidget(meta)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 2, 0, 0)
        action_row.setSpacing(8)

        detail_parts = []
        if str(self.data.get("duration") or "").strip():
            detail_parts.append(str(self.data["duration"]).strip())
        if self.data.get("tracks") not in (None, ""):
            detail_parts.append(f"{self.data['tracks']} TRACKS")
        detail = QLabel(" • ".join(detail_parts) if detail_parts else "LIVESET")
        detail.setObjectName("meta")
        action_row.addWidget(detail, 1)

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("cdTrackPlayButton")
        self.play_button.setProperty("playing", False)
        self.play_button.setFixedSize(42, 34)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.setToolTip("Speel liveset")
        self.play_button.clicked.connect(self._play_clicked)
        action_row.addWidget(self.play_button)
        root.addLayout(action_row)

        self.replace_button = QPushButton("VERVANG FOTO")
        self.replace_button.setObjectName("coverButton")
        self.replace_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.replace_button.clicked.connect(self._cover_clicked)
        root.addWidget(self.replace_button)

        self.upload_progress = QProgressBar()
        self.upload_progress.setObjectName("uploadProgress")
        self.upload_progress.setRange(0, 100)
        self.upload_progress.setTextVisible(False)
        self.upload_progress.setFixedHeight(3)
        self.upload_progress.hide()
        root.addWidget(self.upload_progress)

    @staticmethod
    def _crop_cover(pixmap: QPixmap, width: int, height: int) -> QPixmap:
        if pixmap.isNull():
            return QPixmap()
        scaled = pixmap.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - width) // 2)
        y = max(0, (scaled.height() - height) // 2)
        return scaled.copy(x, y, width, height)

    def _load_cover(self, path: str):
        self._cover_pixmap = QPixmap()
        if path and Path(path).exists():
            self._cover_pixmap = QPixmap(str(path))
        self._render_cover(False)

    def _render_cover(self, zoom: bool):
        if self._cover_pixmap.isNull():
            self.cover.setPixmap(QPixmap())
            self.cover.setText("GEEN COVER")
            return
        width = 370 if zoom else 340
        height = 205 if zoom else 185
        cropped = self._crop_cover(self._cover_pixmap, width, height)
        self.cover.setText("")
        self.cover.setPixmap(cropped)

    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)
        self._render_cover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self._render_cover(False)
        super().leaveEvent(event)

    def _play_clicked(self):
        path = str(self.data.get("audio") or "").strip()
        if path:
            self.play_requested.emit(path)

    def _cover_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Vervang cover",
            "",
            "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if path:
            self.cover_requested.emit(path)

    def set_playing(self, playing: bool):
        self._playing = bool(playing)
        self.play_button.setProperty("playing", self._playing)
        self.play_button.setText("❚❚" if self._playing else "▶")
        self.play_button.setToolTip("Pauzeer liveset" if self._playing else "Speel liveset")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.play_button.update()

    def set_cover(self, path: str):
        self.data["cover"] = path
        self._load_cover(path)

    def animate_upload(self):
        self.upload_progress.setValue(0)
        self.upload_progress.show()
        animation = QPropertyAnimation(self.upload_progress, b"value", self)
        animation.setDuration(520)
        animation.setStartValue(0)
        animation.setEndValue(100)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(self.upload_progress.hide)
        self._upload_animation = animation
        animation.start()

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(360)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()


class LiveSetDialog(QDialog):
    """Editor for a new liveset, including drag/drop cover preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nieuwe Liveset")
        self.setMinimumWidth(540)
        self.audio_path = ""
        self.cover_path = ""
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22)
        root.setSpacing(10)

        heading = QLabel("Nieuwe Liveset")
        heading.setObjectName("detailTitle")
        root.addWidget(heading)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Titel van de liveset")
        root.addWidget(self.title_edit)

        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Artiest / DJ")
        root.addWidget(self.artist_edit)

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("Datum")
        root.addWidget(self.date_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Locatie")
        root.addWidget(self.location_edit)

        self.details_edit = QLineEdit()
        self.details_edit.setPlaceholderText("Duur of aantal tracks — optioneel")
        root.addWidget(self.details_edit)

        audio_row = QHBoxLayout()
        self.audio_label = QLabel("Geen audio gekozen")
        self.audio_label.setObjectName("meta")
        audio_row.addWidget(self.audio_label, 1)
        audio_button = QPushButton("KIES AUDIO")
        audio_button.clicked.connect(self._choose_audio)
        audio_row.addWidget(audio_button)
        root.addLayout(audio_row)

        self.drop_zone = CoverDropZone()
        self.drop_zone.file_selected.connect(self._cover_selected)
        root.addWidget(self.drop_zone)

        self.preview = QLabel("PREVIEW")
        self.preview.setObjectName("cover")
        self.preview.setFixedHeight(180)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.preview)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _choose_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Kies liveset-audio",
            "",
            "Audio (*.mp3 *.wav *.m4a *.flac *.ogg)",
        )
        if path:
            self.audio_path = path
            self.audio_label.setText(Path(path).name)

    def _cover_selected(self, path):
        self.cover_path = path
        pix = QPixmap(path)
        if pix.isNull():
            return
        scaled = LiveSetCard._crop_cover(pix, 320, 180)
        self.preview.setText("")
        self.preview.setPixmap(scaled)

    def get_data(self):
        return {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_edit.text().strip(),
            "date": self.date_edit.text().strip(),
            "location": self.location_edit.text().strip(),
            "duration": self.details_edit.text().strip(),
            "tracks": "",
            "audio": self.audio_path,
            "cover": self.cover_path,
        }

    def accept(self):
        if not self.title_edit.text().strip() or not self.audio_path:
            return
        super().accept()


class LivesetsPage(QWidget):
    """Standalone Livesets section, visually aligned with CD Showcase."""

    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_path = None
        self.cards = []
        self._load_data()
        self._build_ui()

    @property
    def data_dir(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LIVESETS_COVERS.mkdir(parents=True, exist_ok=True)
        return DATA_DIR

    def _load_data(self):
        self.data_dir
        if not LIVESETS_FILE.exists():
            self.items = []
            return
        try:
            data = json.loads(LIVESETS_FILE.read_text(encoding="utf-8"))
            self.items = data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            self.items = []

    def _save_data(self):
        self.data_dir
        LIVESETS_FILE.write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        # Same title scale, spacing and accent language as CD Showcase.
        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("LIVESETS")
        title.setObjectName("showcaseTitle")
        title_col.addWidget(title)
        underline = QFrame()
        underline.setObjectName("showcaseUnderline")
        underline.setFixedHeight(2)
        underline.setMaximumWidth(150)
        title_col.addWidget(underline)
        subtitle = QLabel("DJ sets, recordings en live sessions")
        subtitle.setObjectName("showcaseInfo")
        title_col.addWidget(subtitle)
        header.addLayout(title_col, 1)

        add_button = QPushButton("+ NIEUWE LIVESET")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(self._new_liveset)
        header.addWidget(add_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(10, 10, 10, 20)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(18)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet(self._style())
        self._refresh_cards()

    def _refresh_cards(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.cards.clear()

        if not self.items:
            empty = QLabel("Geen livesets gevonden. Klik op + NIEUWE LIVESET om er één toe te voegen.")
            empty.setObjectName("showcaseInfo")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(empty, 0, 0, 1, 4)
            return

        columns = 4
        for index, data in enumerate(self.items):
            card = LiveSetCard(data, delay_ms=45 * index)
            card.play_requested.connect(self._play_requested)
            card.cover_requested.connect(
                lambda path, d=data, c=card: self._replace_cover(d, c, path)
            )
            self.cards.append(card)
            self.grid.addWidget(card, index // columns, index % columns)

        for column in range(columns):
            self.grid.setColumnStretch(column, 1)
        self._sync_playing_buttons()

    def _new_liveset(self):
        dialog = LiveSetDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        data = dialog.get_data()
        self._copy_cover_and_store(data, data.get("cover", ""))
        self.items.insert(0, data)
        self._save_data()
        self._refresh_cards()

    def _replace_cover(self, data, card, source):
        self._copy_cover_and_store(data, source)
        self._save_data()
        card.set_cover(data.get("cover", ""))
        card.animate_upload()

    def _copy_cover_and_store(self, data, source):
        if not source:
            return
        source_path = Path(source)
        if not source_path.exists():
            return
        LIVESETS_COVERS.mkdir(parents=True, exist_ok=True)
        safe_name = f"liveset_{abs(hash(data.get('title', 'set') + source_path.name))}{source_path.suffix.lower()}"
        destination = LIVESETS_COVERS / safe_name
        try:
            shutil.copy2(source_path, destination)
            data["cover"] = str(destination)
        except OSError:
            pass

    @staticmethod
    def _normalise(path):
        path = str(path or "").strip()
        if not path:
            return ""
        try:
            return str(Path(path).expanduser().resolve()).casefold()
        except OSError:
            return path.casefold()

    def _play_requested(self, path):
        self.active_path = self._normalise(path) or None
        self._sync_playing_buttons()
        self.play_mp3.emit(path)

    def set_active_track(self, path):
        self.active_path = self._normalise(path) or None
        self._sync_playing_buttons()

    def clear_active_track(self):
        self.active_path = None
        self._sync_playing_buttons()

    def set_playback_state(self, state):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if state != QMediaPlayer.PlaybackState.PlayingState:
                self.clear_active_track()
        except Exception:
            self.clear_active_track()

    def _sync_playing_buttons(self):
        for card in self.cards:
            card.set_playing(
                bool(self.active_path)
                and self._normalise(card.data.get("audio")) == self.active_path
            )

    @staticmethod
    def _style():
        return """
        QWidget { background:#0b0b0f; color:#f5f5f7; font-family:'Segoe UI Semibold'; }
        QPushButton { background:#18181f; color:#fff; border:1px solid #30303a;
            border-radius:7px; padding:8px 14px; font-size:12px; font-weight:800; }
        QPushButton:hover { background:#24242c; border-color:#555563; }
        QLineEdit { background:#121217; color:#fff; border:1px solid #30303a;
            border-radius:8px; padding:10px 12px; font-size:13px; }
        QLabel#showcaseTitle { color:#fff; font-size:26px; font-weight:900; }
        QLabel#showcaseInfo { color:#9b9ba6; font-size:13px; }
        QFrame#showcaseUnderline { background:#ffcf72; border-radius:1px; }
        QFrame#releaseCard { background:#121217; border:1px solid #292933; border-radius:10px; }
        QFrame#releaseCard[hovered="true"] { background:#17171e; border-color:#5b5b6b; }
        QLabel#cover { background:#07070a; color:#666671; border:1px solid #2a2a33; border-radius:6px; }
        QLabel#artist { color:#ffcf72; font-size:13px; font-weight:800; }
        QLabel#title { color:#fff; font-size:16px; font-weight:900; }
        QLabel#meta { color:#858591; font-size:12px; }
        QPushButton#cdTrackPlayButton {
            background:#6b1717; color:#fff; border:1px solid #8f2929;
            border-radius:7px; padding:4px; font-size:15px; font-weight:900;
        }
        QPushButton#cdTrackPlayButton:hover { background:#842020; border-color:#b43a3a; }
        QPushButton#cdTrackPlayButton[playing="true"] {
            background:#1f7a3d; border-color:#35a65b;
        }
        QPushButton#cdTrackPlayButton[playing="true"]:hover {
            background:#29934a; border-color:#4fc874;
        }
        QPushButton#coverButton { background:transparent; color:#858591;
            border:1px solid #30303a; border-radius:6px; padding:5px 9px; font-size:10px; }
        QPushButton#coverButton:hover { color:#fff; border-color:#ffcf72; background:#1a1a20; }
        QProgressBar#uploadProgress { background:#202027; border:0; border-radius:1px; }
        QProgressBar#uploadProgress::chunk { background:#ffcf72; border-radius:1px; }
        QFrame#coverDropZone { background:#101014; border:2px dashed #34343f; border-radius:9px; }
        QFrame#coverDropZone[dragging="true"] { background:#18181e; border-color:#ffcf72; }
        QLabel#uploadIcon { color:#ffcf72; font-size:32px; }
        QLabel#uploadTitle { color:#fff; font-size:14px; font-weight:900; }
        QLabel#uploadHint { color:#777782; font-size:11px; }
        QScrollBar:vertical { background:#0b0b0f; width:10px; }
        QScrollBar::handle:vertical { background:#2c2c36; border-radius:5px; min-height:30px; }
        """
