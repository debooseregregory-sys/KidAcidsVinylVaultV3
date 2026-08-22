from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"
COVERS_DIR = DATA_DIR / "liveset_covers"


class LivesetEditDialog(QDialog):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = dict(data or {})
        self.setWindowTitle("Liveset bewerken")
        self.setMinimumWidth(520)

        root = QVBoxLayout(self)
        form = QFormLayout()
        self.fields = {}
        for key, label in [
            ("title", "Titel"),
            ("artist", "Artiest / DJ"),
            ("date", "Datum"),
            ("location", "Locatie"),
            ("duration", "Duur / tracks"),
            ("audio", "Audio bestand"),
        ]:
            edit = QLineEdit(str(self.data.get(key) or ""))
            self.fields[key] = edit
            form.addRow(label, edit)
        root.addLayout(form)

        cover_row = QHBoxLayout()
        self.cover_label = QLabel("Geen cover")
        self.cover_label.setObjectName("dialogCover")
        self.cover_label.setFixedSize(220, 124)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_row.addWidget(self.cover_label)
        choose = QPushButton("KIES / VERVANG COVER")
        choose.clicked.connect(self.choose_cover)
        cover_row.addWidget(choose, 1, Qt.AlignmentFlag.AlignCenter)
        root.addLayout(cover_row)
        self._show_cover(str(self.data.get("cover") or ""))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.setStyleSheet("""
            QDialog{background:#0e0e12;color:#fff;}
            QLabel{color:#c9c9d0;font-size:12px;}
            QLineEdit{background:#15151b;color:#fff;border:1px solid #30303a;border-radius:7px;padding:9px;}
            QPushButton{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:7px;padding:9px 12px;font-weight:800;}
            QPushButton:hover{border-color:#ffcf72;}
            QLabel#dialogCover{background:#07070a;border:1px solid #2a2a33;border-radius:7px;color:#666671;}
        """)

    def choose_cover(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kies cover", "", "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:
            return
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        dest = COVERS_DIR / f"cover_{abs(hash(Path(path).name + str(Path(path).stat().st_mtime_ns)))}{Path(path).suffix.lower()}"
        shutil.copy2(path, dest)
        self.data["cover"] = str(dest)
        self._show_cover(str(dest))

    def _show_cover(self, path):
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            self.cover_label.setPixmap(QPixmap())
            self.cover_label.setText("Geen cover")
            return
        size = self.cover_label.size()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        self.cover_label.setText("")
        self.cover_label.setPixmap(scaled.copy(x, y, size.width(), size.height()))

    def result_data(self):
        result = {k: e.text().strip() for k, e in self.fields.items()}
        result["cover"] = str(self.data.get("cover") or "")
        return result


class LivesetCard(QFrame):
    play_requested = Signal(dict)
    edit_requested = Signal(dict)
    delete_requested = Signal(dict)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = dict(data)
        self._build()

    def _build(self):
        self.setObjectName("liveCard")
        self.setFixedWidth(270)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)

        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("liveCover")
        self.cover.setFixedSize(254, 143)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.cover)
        self._show_cover()

        artist = QLabel(str(self.data.get("artist") or "LIVESET"))
        artist.setObjectName("liveArtist")
        root.addWidget(artist)

        title = QLabel(str(self.data.get("title") or "(geen titel)"))
        title.setObjectName("liveTitle")
        title.setWordWrap(True)
        root.addWidget(title)

        meta = " • ".join(x for x in [str(self.data.get("date") or ""), str(self.data.get("location") or "")] if x)
        meta_label = QLabel(meta or "Geen datum / locatie")
        meta_label.setObjectName("liveMeta")
        meta_label.setWordWrap(True)
        root.addWidget(meta_label)

        actions = QHBoxLayout()
        actions.setSpacing(5)
        play = QPushButton("▶")
        play.setObjectName("livePlay")
        play.setFixedSize(40, 32)
        play.clicked.connect(lambda: self.play_requested.emit(self.data))
        actions.addWidget(play)

        edit = QPushButton("BEWERK")
        edit.setObjectName("liveSmall")
        edit.clicked.connect(lambda: self.edit_requested.emit(self.data))
        actions.addWidget(edit)

        upload = QPushButton("FOTO")
        upload.setObjectName("liveSmall")
        upload.clicked.connect(self._upload)
        actions.addWidget(upload)
        root.addLayout(actions)

    def _show_cover(self):
        path = str(self.data.get("cover") or "")
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            return
        size = self.cover.size()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        self.cover.setText("")
        self.cover.setPixmap(scaled.copy(x, y, size.width(), size.height()))

    def _upload(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kies cover", "", "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:
            return
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        dest = COVERS_DIR / f"cover_{abs(hash(Path(path).name + str(Path(path).stat().st_mtime_ns)))}{Path(path).suffix.lower()}"
        shutil.copy2(path, dest)
        self.data["cover"] = str(dest)
        self._show_cover()
        self.edit_requested.emit(self.data)


class LivesetsLibraryPage(QWidget):
    """The single Livesets section: compact showcase plus inline editing."""

    open_requested = Signal(dict)
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.cards = []
        self._build()
        self.reload()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(7)

        title = QLabel("LIVESETS")
        title.setObjectName("showcaseTitle")
        root.addWidget(title)
        line = QFrame()
        line.setObjectName("showcaseLine")
        line.setFixedHeight(2)
        line.setMaximumWidth(150)
        root.addWidget(line)

        header = QHBoxLayout()
        sub = QLabel("Livesets — beheer, covers en afspelen in één overzicht")
        sub.setObjectName("showcaseSub")
        header.addWidget(sub)
        header.addStretch(1)
        add = QPushButton("＋ NIEUWE LIVESET")
        add.setObjectName("newButton")
        add.clicked.connect(self.new_liveset)
        header.addWidget(add)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        scroll.setStyleSheet("QScrollArea{border:0;background:transparent;}")
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(8, 14, 8, 20)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.content)
        root.addWidget(scroll, 1)

        self.setStyleSheet("""
            QLabel#showcaseTitle{color:#fff;font-size:26px;font-weight:900;}
            QLabel#showcaseSub{color:#858591;font-size:13px;}
            QFrame#showcaseLine{background:#ffcf72;border-radius:1px;}
            QFrame#liveCard{background:#121217;border:1px solid #292933;border-radius:9px;}
            QFrame#liveCard:hover{background:#17171e;border-color:#5b5b6b;}
            QLabel#liveCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:6px;}
            QLabel#liveArtist{color:#ffcf72;font-size:10px;font-weight:900;}
            QLabel#liveTitle{color:#fff;font-size:14px;font-weight:900;}
            QLabel#liveMeta{color:#858591;font-size:10px;}
            QPushButton#livePlay{background:#6b1717;color:#fff;border:1px solid #8f2929;border-radius:7px;font-size:14px;font-weight:900;}
            QPushButton#livePlay:hover{background:#842020;border-color:#b43a3a;}
            QPushButton#liveSmall,QPushButton#newButton{background:#18181f;color:#ddd;border:1px solid #30303a;border-radius:6px;padding:7px 9px;font-size:10px;font-weight:900;}
            QPushButton#liveSmall:hover,QPushButton#newButton:hover{border-color:#ffcf72;color:#fff;}
        """)

    def reload(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards = []
        try:
            self.items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError, json.JSONDecodeError):
            self.items = []
        if not self.items:
            empty = QLabel("Nog geen livesets. Gebruik NIEUWE LIVESET om er één toe te voegen.")
            empty.setObjectName("showcaseSub")
            self.grid.addWidget(empty, 0, 0)
            return
        for index, data in enumerate(self.items):
            card = LivesetCard(data)
            card.play_requested.connect(self.open_requested.emit)
            card.edit_requested.connect(self._edit)
            self.cards.append(card)
            self.grid.addWidget(card, index // 4, index % 4)

    def _write(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LIVESETS_FILE.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
        self.changed.emit()

    def _edit(self, data):
        try:
            index = next(i for i, item in enumerate(self.items) if item.get("audio") == data.get("audio") and item.get("title") == data.get("title"))
        except StopIteration:
            index = -1
        dialog = LivesetEditDialog(data, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        result = dialog.result_data()
        if index >= 0:
            self.items[index] = result
        else:
            self.items.append(result)
        self._write()
        self.reload()

    def new_liveset(self):
        self._edit({"title": "", "artist": "", "date": "", "location": "", "duration": "", "audio": "", "cover": ""})
