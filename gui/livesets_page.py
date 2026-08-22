# ============================================================
# KID ACID'S VINYLVAULT V3
# LIVESETS SHOWCASE
# ============================================================

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, Signal
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
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("coverDropZone")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)
        icon = QLabel("＋")
        icon.setObjectName("uploadIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        title = QLabel("Upload cover")
        title.setObjectName("uploadTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        hint = QLabel("Sleep een afbeelding hierheen of klik om te kiezen")
        hint.setObjectName("uploadHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        self.icon = icon

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            path, _ = QFileDialog.getOpenFileName(
                self, "Kies cover", "", "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)"
            )
            if path:
                self.file_selected.emit(path)
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if any(Path(u.toLocalFile()).suffix.lower() in IMAGE_EXTENSIONS for u in event.mimeData().urls()):
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self); self.style().polish(self)
            self.icon.setText("✦")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self); self.style().polish(self)
        self.icon.setText("＋")
        event.accept()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and Path(path).suffix.lower() in IMAGE_EXTENSIONS:
                self.file_selected.emit(path)
                break
        self.setProperty("dragging", False)
        self.style().unpolish(self); self.style().polish(self)
        self.icon.setText("＋")
        event.acceptProposedAction()


class LiveSetCard(QFrame):
    play_requested = Signal(str)
    cover_requested = Signal(str)

    CARD_WIDTH = 300
    COVER_WIDTH = 278
    COVER_HEIGHT = 156

    def __init__(self, data: dict, delay_ms=0, parent=None):
        super().__init__(parent)
        self.data = data
        self._playing = False
        self._cover_pixmap = QPixmap()
        self._fade = None
        self.setObjectName("livesetCard")
        self._build()
        QTimer.singleShot(delay_ms, self._fade_in)

    def _build(self):
        self.setFixedWidth(self.CARD_WIDTH)
        self.setMinimumHeight(282)
        self.setMaximumHeight(310)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("livesetCover")
        self.cover.setFixedSize(self.COVER_WIDTH, self.COVER_HEIGHT)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignHCenter)
        self._load_cover(self.data.get("cover", ""))

        self.title = QLabel(str(self.data.get("title") or "(geen titel)"))
        self.title.setObjectName("livesetTitle")
        self.title.setWordWrap(True)
        self.title.setMaximumHeight(38)
        root.addWidget(self.title)

        self.subtitle = QLabel(self._subtitle())
        self.subtitle.setObjectName("livesetSubtitle")
        self.subtitle.setWordWrap(True)
        self.subtitle.setMaximumHeight(34)
        root.addWidget(self.subtitle)

        row = QHBoxLayout()
        row.setContentsMargins(0, 2, 0, 0)
        row.setSpacing(8)
        details = self.data.get("duration") or self.data.get("tracks") or "LIVESET"
        self.details = QLabel(str(details))
        self.details.setObjectName("livesetMeta")
        row.addWidget(self.details, 1)

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("livesetPlayButton")
        self.play_button.setProperty("playing", False)
        self.play_button.setFixedSize(38, 34)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.clicked.connect(self._play_clicked)
        row.addWidget(self.play_button)
        root.addLayout(row)

        self.replace_button = QPushButton("VERVANG FOTO")
        self.replace_button.setObjectName("livesetCoverButton")
        self.replace_button.setFixedHeight(25)
        self.replace_button.clicked.connect(self._cover_clicked)
        root.addWidget(self.replace_button)

        self.progress = QProgressBar()
        self.progress.setObjectName("livesetProgress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(2)
        self.progress.hide()
        root.addWidget(self.progress)

    def _subtitle(self):
        parts = [str(self.data.get("artist") or "").strip(), str(self.data.get("date") or "").strip(), str(self.data.get("location") or "").strip()]
        return " • ".join(p for p in parts if p) or "DJ LIVESET"

    @staticmethod
    def crop_cover(pixmap, width, height):
        if pixmap.isNull():
            return QPixmap()
        scaled = pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - width) // 2)
        y = max(0, (scaled.height() - height) // 2)
        return scaled.copy(x, y, width, height)

    def _load_cover(self, path):
        self._cover_pixmap = QPixmap(str(path)) if path and Path(path).exists() else QPixmap()
        self._render_cover()

    def _render_cover(self):
        if self._cover_pixmap.isNull():
            self.cover.clear()
            self.cover.setText("GEEN COVER")
            return
        self.cover.setText("")
        self.cover.setPixmap(self.crop_cover(self._cover_pixmap, self.COVER_WIDTH, self.COVER_HEIGHT))

    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self.style().unpolish(self); self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().unpolish(self); self.style().polish(self)
        super().leaveEvent(event)

    def _play_clicked(self):
        path = str(self.data.get("audio") or "").strip()
        if path:
            self.play_requested.emit(path)

    def _cover_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Vervang cover", "", "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)")
        if path:
            self.cover_requested.emit(path)

    def set_playing(self, playing):
        self._playing = bool(playing)
        self.play_button.setProperty("playing", self._playing)
        self.play_button.setText("❚❚" if self._playing else "▶")
        self.play_button.style().unpolish(self.play_button); self.play_button.style().polish(self.play_button)
        self.play_button.update()

    def set_cover(self, path):
        self.data["cover"] = path
        self._load_cover(path)

    def animate_upload(self):
        self.progress.setValue(0)
        self.progress.show()
        animation = QPropertyAnimation(self.progress, b"value", self)
        animation.setDuration(500)
        animation.setStartValue(0); animation.setEndValue(100)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(self.progress.hide)
        self._upload_animation = animation
        animation.start()

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(320)
        self._fade.setStartValue(0.0); self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()


class LiveSetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nieuwe Liveset")
        self.setMinimumWidth(520)
        self.audio_path = ""
        self.cover_path = ""
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 22, 22, 22); root.setSpacing(10)
        title = QLabel("Nieuwe Liveset"); title.setObjectName("dialogTitle"); root.addWidget(title)
        self.title_edit = QLineEdit(); self.title_edit.setPlaceholderText("Titel van de liveset"); root.addWidget(self.title_edit)
        self.artist_edit = QLineEdit(); self.artist_edit.setPlaceholderText("Artiest / DJ"); root.addWidget(self.artist_edit)
        self.date_edit = QLineEdit(); self.date_edit.setPlaceholderText("Datum"); root.addWidget(self.date_edit)
        self.location_edit = QLineEdit(); self.location_edit.setPlaceholderText("Locatie"); root.addWidget(self.location_edit)
        self.details_edit = QLineEdit(); self.details_edit.setPlaceholderText("Duur / aantal tracks — optioneel"); root.addWidget(self.details_edit)
        audio_row = QHBoxLayout(); self.audio_label = QLabel("Geen audio gekozen"); audio_row.addWidget(self.audio_label, 1)
        audio = QPushButton("KIES AUDIO"); audio.clicked.connect(self._choose_audio); audio_row.addWidget(audio); root.addLayout(audio_row)
        self.drop_zone = CoverDropZone(); self.drop_zone.file_selected.connect(self._cover_selected); root.addWidget(self.drop_zone)
        self.preview = QLabel("PREVIEW"); self.preview.setObjectName("previewCover"); self.preview.setFixedSize(320, 180); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); root.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignHCenter)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _choose_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kies liveset-audio", "", "Audio (*.mp3 *.wav *.m4a *.flac *.ogg)")
        if path: self.audio_path = path; self.audio_label.setText(Path(path).name)

    def _cover_selected(self, path):
        self.cover_path = path
        pix = LiveSetCard.crop_cover(QPixmap(path), 320, 180)
        if not pix.isNull(): self.preview.setText(""); self.preview.setPixmap(pix)

    def get_data(self):
        return {"title": self.title_edit.text().strip(), "artist": self.artist_edit.text().strip(), "date": self.date_edit.text().strip(), "location": self.location_edit.text().strip(), "duration": self.details_edit.text().strip(), "tracks": "", "audio": self.audio_path, "cover": self.cover_path}

    def accept(self):
        if not self.title_edit.text().strip() or not self.audio_path:
            return
        super().accept()


class LivesetsPage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_path = None
        self.cards = []
        self._load_data()
        self._build_ui()

    def _ensure_dirs(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LIVESETS_COVERS.mkdir(parents=True, exist_ok=True)

    def _load_data(self):
        self._ensure_dirs()
        try:
            data = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
            self.items = data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            self.items = []

    def _save_data(self):
        self._ensure_dirs()
        LIVESETS_FILE.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(18)

        header = QHBoxLayout(); header.setSpacing(20)
        title_col = QVBoxLayout(); title_col.setSpacing(5)
        title = QLabel("Livesets"); title.setObjectName("livesetsHeader"); title_col.addWidget(title)
        line = QFrame(); line.setObjectName("livesetsAccent"); line.setFixedSize(92, 2); title_col.addWidget(line)
        info = QLabel("Persoonlijke showcase voor DJ sets en live recordings"); info.setObjectName("livesetsInfo"); title_col.addWidget(info)
        header.addLayout(title_col, 1)
        add = QPushButton("＋  NIEUWE LIVESET"); add.setObjectName("livesetsAdd"); add.clicked.connect(self._new_liveset); header.addWidget(add, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget(); self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(4, 8, 4, 24); self.grid.setHorizontalSpacing(18); self.grid.setVerticalSpacing(18)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.content); root.addWidget(self.scroll, 1)
        self.setStyleSheet(self._style())
        self._refresh_cards()

    def _refresh_cards(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.cards.clear()
        if not self.items:
            empty = QLabel("Nog geen livesets. Voeg hierboven je eerste liveset toe."); empty.setObjectName("emptyState"); empty.setAlignment(Qt.AlignmentFlag.AlignCenter); self.grid.addWidget(empty, 0, 0, 1, 3); return
        # Three compact cards on desktop. This deliberately prevents the old oversized columns.
        columns = 3
        for index, data in enumerate(self.items):
            card = LiveSetCard(data, 45 * index)
            card.play_requested.connect(self._play_requested)
            card.cover_requested.connect(lambda path, d=data, c=card: self._replace_cover(d, c, path))
            self.cards.append(card)
            self.grid.addWidget(card, index // columns, index % columns)
        self._sync_playing_buttons()

    def _new_liveset(self):
        dialog = LiveSetDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        data = dialog.get_data(); self._copy_cover(data, data.get("cover", "")); self.items.insert(0, data); self._save_data(); self._refresh_cards()

    def _replace_cover(self, data, card, source):
        self._copy_cover(data, source); self._save_data(); card.set_cover(data.get("cover", "")); card.animate_upload()

    def _copy_cover(self, data, source):
        if not source: return
        source_path = Path(source)
        if not source_path.exists(): return
        self._ensure_dirs()
        safe = f"liveset_{abs(hash(data.get('title', 'set') + source_path.name))}{source_path.suffix.lower()}"
        destination = LIVESETS_COVERS / safe
        try:
            shutil.copy2(source_path, destination); data["cover"] = str(destination)
        except OSError: pass

    @staticmethod
    def _normalise(path):
        path = str(path or "").strip()
        if not path: return ""
        try: return str(Path(path).expanduser().resolve()).casefold()
        except OSError: return path.casefold()

    def _play_requested(self, path):
        self.active_path = self._normalise(path) or None; self._sync_playing_buttons(); self.play_mp3.emit(path)

    def set_active_track(self, path): self.active_path = self._normalise(path) or None; self._sync_playing_buttons()
    def clear_active_track(self): self.active_path = None; self._sync_playing_buttons()

    def set_playback_state(self, state):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if state != QMediaPlayer.PlaybackState.PlayingState: self.clear_active_track()
        except Exception: self.clear_active_track()

    def _sync_playing_buttons(self):
        for card in self.cards:
            card.set_playing(bool(self.active_path) and self._normalise(card.data.get("audio")) == self.active_path)

    @staticmethod
    def _style():
        return """
        QWidget { background:#0b0b0f; color:#f2f2f5; font-family:'Segoe UI'; }
        QScrollArea { border:none; background:transparent; }
        QLabel#livesetsHeader { color:#ffffff; font-size:28px; font-weight:800; }
        QLabel#livesetsInfo { color:#8e8e9a; font-size:12px; }
        QFrame#livesetsAccent { background:#ffcf72; border-radius:1px; }
        QPushButton#livesetsAdd { background:#18181f; color:#ffffff; border:1px solid #30303a; border-radius:7px; padding:9px 14px; font-size:11px; font-weight:800; }
        QPushButton#livesetsAdd:hover { background:#24242c; border-color:#ffcf72; }
        QFrame#livesetCard { background:#121217; border:1px solid #292933; border-radius:10px; }
        QFrame#livesetCard:hover { background:#17171e; border-color:#4a4a56; }
        QLabel#livesetCover { background:#07070a; color:#5e5e69; border:1px solid #2a2a33; border-radius:6px; }
        QLabel#livesetTitle { color:#ffffff; font-size:15px; font-weight:800; }
        QLabel#livesetSubtitle { color:#a4a4af; font-size:11px; }
        QLabel#livesetMeta { color:#777783; font-size:10px; }
        QPushButton#livesetPlayButton { background:#6b1717; color:#ffffff; border:1px solid #8f2929; border-radius:17px; font-size:14px; font-weight:900; }
        QPushButton#livesetPlayButton:hover { background:#842020; border-color:#b43a3a; }
        QPushButton#livesetPlayButton[playing="true"] { background:#1f7a3d; border-color:#35a65b; }
        QPushButton#livesetPlayButton[playing="true"]:hover { background:#29934a; border-color:#4fc874; }
        QPushButton#livesetCoverButton { background:transparent; color:#777783; border:1px solid #30303a; border-radius:5px; font-size:9px; font-weight:700; }
        QPushButton#livesetCoverButton:hover { color:#ffffff; border-color:#ffcf72; background:#1a1a20; }
        QProgressBar#livesetProgress { background:#22222a; border:0; }
        QProgressBar#livesetProgress::chunk { background:#ffcf72; }
        QLabel#emptyState { color:#777783; font-size:13px; min-height:120px; }
        QFrame#coverDropZone { background:#101014; border:2px dashed #34343f; border-radius:9px; min-height:120px; }
        QFrame#coverDropZone[dragging="true"] { background:#18181e; border-color:#ffcf72; }
        QLabel#uploadIcon { color:#ffcf72; font-size:30px; }
        QLabel#uploadTitle { color:#ffffff; font-size:14px; font-weight:800; }
        QLabel#uploadHint { color:#777783; font-size:11px; }
        QLabel#previewCover { background:#07070a; color:#666671; border:1px solid #2a2a33; border-radius:6px; }
        QLabel#dialogTitle { color:#ffffff; font-size:22px; font-weight:800; }
        QLineEdit { background:#121217; color:#ffffff; border:1px solid #30303a; border-radius:7px; padding:9px; }
        QLineEdit:focus { border-color:#ffcf72; }
        QScrollBar:vertical { background:#0b0b0f; width:9px; }
        QScrollBar::handle:vertical { background:#2c2c36; border-radius:4px; min-height:30px; }
        """
