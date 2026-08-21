# ============================================================
# KID ACID'S VINYLVAULT V3
# LIVESETS SHOWCASE
# ============================================================

"""Modern dark Livesets page.

The project is a PySide6 desktop application, so this component uses
native Qt widgets rather than introducing a separate React/Tailwind UI.
Liveset metadata is kept in a small JSON file and cover images are copied
into data/liveset_covers so the feature remains completely local.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QMimeData,
    QPropertyAnimation,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
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


class CoverDropZone(QFrame):
    """Clickable + drag/drop cover uploader with visual drag-over state."""

    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("coverDropZone")
        self.setMinimumHeight(180)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

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
        hint.setWordWrap(True)
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
            self.style().unpolish(self)
            self.style().polish(self)
            self.icon.setText("✦")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.icon.setText("＋")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            if path and Path(path).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                self.file_selected.emit(path)
                break
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self.icon.setText("＋")
        event.acceptProposedAction()

    @staticmethod
    def _has_image(mime: QMimeData) -> bool:
        for url in mime.urls():
            if Path(url.toLocalFile()).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                return True
        return False


class LiveSetCard(QFrame):
    """Responsive liveset card with hover, upload and playback feedback."""

    play_requested = Signal(str)
    cover_requested = Signal(str)

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self._playing = False
        self._fade = None
        self.setObjectName("livesetCard")
        self.setMinimumWidth(300)
        self.setMaximumWidth(460)
        self._build()
        self._fade_in()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 14)
        root.setSpacing(10)

        cover_wrap = QFrame()
        cover_wrap.setObjectName("coverWrap")
        cover_layout = QVBoxLayout(cover_wrap)
        cover_layout.setContentsMargins(0, 0, 0, 0)

        self.cover = QLabel()
        self.cover.setObjectName("livesetCover")
        self.cover.setMinimumHeight(170)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setScaledContents(False)
        cover_layout.addWidget(self.cover)

        self.cover_overlay = QLabel("VERVANG FOTO")
        self.cover_overlay.setObjectName("coverOverlay")
        self.cover_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_overlay.hide()
        cover_layout.addWidget(self.cover_overlay)
        root.addWidget(cover_wrap)

        self._set_cover(self.data.get("cover", ""))

        title_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel(str(self.data.get("title") or "Untitled Liveset"))
        title.setObjectName("livesetTitle")
        title.setWordWrap(True)
        title_col.addWidget(title)

        meta = " • ".join(
            value for value in (
                str(self.data.get("date") or "").strip(),
                str(self.data.get("location") or self.data.get("artist") or "").strip(),
            ) if value
        )
        meta_label = QLabel(meta or "Geen datum / locatie")
        meta_label.setObjectName("livesetMeta")
        meta_label.setWordWrap(True)
        title_col.addWidget(meta_label)
        title_row.addLayout(title_col, 1)

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("livesetPlayButton")
        self.play_button.setFixedSize(48, 48)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.setToolTip("Speel liveset")
        self.play_button.clicked.connect(self._play_clicked)
        title_row.addWidget(self.play_button, 0, Qt.AlignmentFlag.AlignCenter)
        root.addLayout(title_row)

        bottom = QHBoxLayout()
        details = []
        duration = str(self.data.get("duration") or "").strip()
        tracks = self.data.get("tracks")
        if duration:
            details.append(duration)
        if tracks not in (None, ""):
            details.append(f"{tracks} tracks")
        detail_label = QLabel(" • ".join(details) if details else "LIVESET")
        detail_label.setObjectName("livesetDetail")
        bottom.addWidget(detail_label)
        bottom.addStretch()

        self.replace_button = QPushButton("Vervang foto")
        self.replace_button.setObjectName("coverButton")
        self.replace_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.replace_button.clicked.connect(self._cover_clicked)
        bottom.addWidget(self.replace_button)
        root.addLayout(bottom)

        self.upload_progress = QProgressBar()
        self.upload_progress.setObjectName("uploadProgress")
        self.upload_progress.setRange(0, 100)
        self.upload_progress.setValue(0)
        self.upload_progress.setTextVisible(False)
        self.upload_progress.hide()
        root.addWidget(self.upload_progress)

    def _set_cover(self, path):
        pix = QPixmap(str(path)) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            self.cover.setText("GEEN COVER")
            return
        scaled = pix.scaled(
            720,
            405,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.cover.setPixmap(scaled)

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
        self._set_cover(path)

    def _fade_in(self):
        # Staggered fade-in without an external animation dependency.
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(360)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(40, self._fade.start)


class LiveSetDialog(QDialog):
    """Small editor used to add a local liveset and its cover."""

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
        root.setSpacing(12)

        title = QLabel("Nieuwe Liveset")
        title.setObjectName("dialogTitle")
        root.addWidget(title)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Titel van de liveset")
        root.addWidget(self.title_edit)

        self.date_edit = QLineEdit()
        self.date_edit.setPlaceholderText("Datum — bijvoorbeeld 22-08-2026")
        root.addWidget(self.date_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Locatie of artiest")
        root.addWidget(self.location_edit)

        self.details_edit = QLineEdit()
        self.details_edit.setPlaceholderText("Duur / aantal tracks — optioneel")
        root.addWidget(self.details_edit)

        audio_row = QHBoxLayout()
        self.audio_label = QLabel("Geen liveset-audio gekozen")
        self.audio_label.setObjectName("dialogMuted")
        audio_row.addWidget(self.audio_label, 1)
        audio_button = QPushButton("Kies audio")
        audio_button.clicked.connect(self._choose_audio)
        audio_row.addWidget(audio_button)
        root.addLayout(audio_row)

        self.drop_zone = CoverDropZone()
        self.drop_zone.file_selected.connect(self._cover_selected)
        root.addWidget(self.drop_zone)

        self.preview = QLabel("Preview verschijnt hier")
        self.preview.setObjectName("dialogPreview")
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
        if not pix.isNull():
            self.preview.setPixmap(
                pix.scaled(
                    320,
                    180,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def get_data(self):
        return {
            "title": self.title_edit.text().strip(),
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
    """Dark, modern Livesets section integrated with VinylVault's MP3 player."""

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
            self.items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8"))
            if not isinstance(self.items, list):
                self.items = []
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
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(18)

        header = QHBoxLayout()
        heading_col = QVBoxLayout()
        heading_col.setSpacing(4)

        heading = QLabel("Livesets")
        heading.setObjectName("livesetsHeading")
        heading_col.addWidget(heading)

        underline = QFrame()
        underline.setObjectName("headingGlow")
        underline.setFixedHeight(2)
        underline.setMaximumWidth(180)
        heading_col.addWidget(underline)

        subtitle = QLabel("Je favoriete DJ-sets, recordings en live sessions op één plek.")
        subtitle.setObjectName("livesetsSubtitle")
        heading_col.addWidget(subtitle)
        header.addLayout(heading_col, 1)

        add_button = QPushButton("＋  NIEUWE LIVESET")
        add_button.setObjectName("addLivesetButton")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(self._new_liveset)
        header.addWidget(add_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(2, 4, 8, 20)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet(self._style())
        self._refresh_cards()

    def _refresh_cards(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.cards.clear()

        if not self.items:
            empty = QFrame()
            empty.setObjectName("emptyLivesets")
            layout = QVBoxLayout(empty)
            layout.setContentsMargins(30, 40, 30, 40)
            icon = QLabel("♫")
            icon.setObjectName("emptyIcon")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon)
            text = QLabel("Nog geen livesets")
            text.setObjectName("emptyTitle")
            text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(text)
            hint = QLabel("Klik op NIEUWE LIVESET om je eerste set toe te voegen.")
            hint.setObjectName("emptyHint")
            hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(hint)
            self.grid.addWidget(empty, 0, 0, 1, 3)
            return

        columns = 3
        for index, data in enumerate(self.items):
            card = LiveSetCard(data)
            card.play_requested.connect(self._play_requested)
            card.cover_requested.connect(lambda path, d=data, c=card: self._replace_cover(d, c, path))
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
        self._animate_upload(card)

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

    def _animate_upload(self, card):
        progress = card.upload_progress
        progress.setValue(0)
        progress.show()
        animation = QPropertyAnimation(progress, b"value", progress)
        animation.setDuration(500)
        animation.setStartValue(0)
        animation.setEndValue(100)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(progress.hide)
        progress._animation = animation
        animation.start()

    def _play_requested(self, path):
        self.active_path = str(Path(path).resolve()).casefold()
        self._sync_playing_buttons()
        self.play_mp3.emit(path)

    def set_active_track(self, path):
        try:
            self.active_path = str(Path(path).resolve()).casefold()
        except OSError:
            self.active_path = str(path or "").casefold()
        self._sync_playing_buttons()

    def clear_active_track(self):
        self.active_path = None
        self._sync_playing_buttons()

    def set_playback_state(self, state):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if state != QMediaPlayer.PlaybackState.PlayingState:
                self.clear_active_track()
            else:
                self._sync_playing_buttons()
        except Exception:
            self.clear_active_track()

    def _sync_playing_buttons(self):
        for card in self.cards:
            path = str(card.data.get("audio") or "").strip()
            try:
                normalised = str(Path(path).resolve()).casefold()
            except OSError:
                normalised = path.casefold()
            card.set_playing(bool(self.active_path and normalised == self.active_path))

    @staticmethod
    def _style():
        return """
        QWidget { background:#0b0b0f; color:#f3f3f6; font-family:'Segoe UI'; }
        QLabel#livesetsHeading { color:#ffffff; font-size:30px; font-weight:900; }
        QLabel#livesetsSubtitle { color:#777784; font-size:13px; }
        QFrame#headingGlow { background:#4d5dff; border-radius:1px; }
        QPushButton#addLivesetButton { background:#171721; color:#e8e9ff; border:1px solid #343450; border-radius:9px; padding:10px 15px; font-weight:800; }
        QPushButton#addLivesetButton:hover { background:#202034; border-color:#5968ff; }
        QFrame#livesetCard { background:#111117; border:1px solid #272733; border-radius:14px; }
        QFrame#livesetCard:hover { background:#15151c; border-color:#41415a; }
        QFrame#coverWrap { background:#08080c; border-radius:10px; }
        QLabel#livesetCover { background:#08080c; color:#62626e; border-radius:10px; min-height:170px; }
        QPushButton#livesetPlayButton { background:#6b1717; color:white; border:1px solid #922e2e; border-radius:24px; font-size:18px; font-weight:900; }
        QPushButton#livesetPlayButton:hover { background:#842020; border-color:#bd4444; }
        QPushButton#livesetPlayButton[playing="true"] { background:#1f7a3d; border-color:#42bd69; }
        QPushButton#livesetPlayButton[playing="true"]:hover { background:#29934a; }
        QLabel#livesetTitle { color:#ffffff; font-size:17px; font-weight:900; }
        QLabel#livesetMeta { color:#9696a4; font-size:12px; }
        QLabel#livesetDetail { color:#686875; font-size:11px; font-weight:800; letter-spacing:1px; }
        QPushButton#coverButton { background:transparent; color:#8f90a0; border:1px solid #2d2d38; border-radius:7px; padding:6px 9px; font-size:11px; }
        QPushButton#coverButton:hover { color:#ffffff; border-color:#5968ff; }
        QProgressBar#uploadProgress { background:#181820; border:0; border-radius:2px; height:3px; }
        QProgressBar#uploadProgress::chunk { background:#5968ff; border-radius:2px; }
        QFrame#emptyLivesets { background:#101016; border:1px dashed #343443; border-radius:14px; }
        QLabel#emptyIcon { color:#5968ff; font-size:42px; }
        QLabel#emptyTitle { color:#ffffff; font-size:20px; font-weight:900; }
        QLabel#emptyHint { color:#777784; font-size:13px; }
        QFrame#coverDropZone { background:#111119; border:2px dashed #343450; border-radius:12px; }
        QFrame#coverDropZone[dragging="true"] { background:#17172a; border-color:#5968ff; }
        QLabel#uploadIcon { color:#5968ff; font-size:34px; font-weight:300; }
        QLabel#uploadTitle { color:#f0f0f6; font-size:14px; font-weight:900; }
        QLabel#uploadHint { color:#777784; font-size:11px; }
        QLabel#dialogTitle { color:#fff; font-size:22px; font-weight:900; }
        QLabel#dialogMuted { color:#777784; }
        QLabel#dialogPreview { background:#09090d; border:1px solid #292933; border-radius:9px; color:#666672; }
        QLineEdit { background:#121219; color:#fff; border:1px solid #30303c; border-radius:8px; padding:9px 11px; }
        QLineEdit:focus { border-color:#5968ff; }
        QScrollBar:vertical { background:#0b0b0f; width:10px; margin:0; }
        QScrollBar::handle:vertical { background:#2c2c38; border-radius:5px; min-height:30px; }
        QScrollBar::handle:vertical:hover { background:#414151; }
        """
