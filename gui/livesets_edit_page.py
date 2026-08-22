from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"
COVERS_DIR = DATA_DIR / "liveset_covers"


class LivesetsEditPage(QWidget):
    """Dedicated Livesets Library/Edit page, separate from the Showcase."""
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.current_index = -1
        self._build()
        self.reload()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(10)
        title = QLabel("LIVESETS")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        line = QFrame()
        line.setObjectName("pageLine")
        line.setFixedHeight(2)
        line.setMaximumWidth(150)
        root.addWidget(line)
        root.addWidget(QLabel("Library & bewerken — de Showcase blijft een aparte weergave."))

        body = QHBoxLayout()
        body.setSpacing(14)
        self.list = QListWidget()
        self.list.setFixedWidth(300)
        self.list.currentRowChanged.connect(self.select)
        body.addWidget(self.list)

        panel = QFrame()
        panel.setObjectName("editPanel")
        form = QVBoxLayout(panel)
        form.setContentsMargins(18, 18, 18, 18)
        form.setSpacing(8)
        self.fields = {}
        for key, label in [("title", "Titel"), ("artist", "Artiest / DJ"), ("date", "Datum"), ("location", "Locatie"), ("duration", "Duur / tracks"), ("audio", "Audio bestand")]:
            lab = QLabel(label.upper())
            lab.setObjectName("fieldLabel")
            form.addWidget(lab)
            edit = QLineEdit()
            self.fields[key] = edit
            form.addWidget(edit)

        cover_row = QHBoxLayout()
        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("editCover")
        self.cover.setFixedSize(300, 169)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_row.addWidget(self.cover)
        upload = QPushButton("VERVANG FOTO")
        upload.clicked.connect(self.choose_cover)
        cover_row.addWidget(upload, 0, Qt.AlignmentFlag.AlignCenter)
        form.addLayout(cover_row)
        form.addStretch(1)

        actions = QHBoxLayout()
        new_btn = QPushButton("＋ NIEUWE LIVESET")
        new_btn.clicked.connect(self.new_item)
        delete = QPushButton("VERWIJDER")
        delete.clicked.connect(self.delete_current)
        save = QPushButton("OPSLAAN")
        save.setObjectName("saveButton")
        save.clicked.connect(self.save)
        actions.addWidget(new_btn)
        actions.addStretch(1)
        actions.addWidget(delete)
        actions.addWidget(save)
        form.addLayout(actions)
        body.addWidget(panel, 1)
        root.addLayout(body, 1)

        self.setStyleSheet("""
            QLabel#pageTitle{color:#fff;font-size:26px;font-weight:900;}
            QFrame#pageLine{background:#ffcf72;border-radius:1px;}
            QListWidget,QFrame#editPanel{background:#121217;border:1px solid #292933;border-radius:9px;}
            QListWidget{padding:6px;color:#ddd;}
            QListWidget::item{padding:12px 10px;border-radius:6px;}
            QListWidget::item:selected{background:#24242c;color:#ffcf72;}
            QLabel#fieldLabel{color:#858591;font-size:10px;font-weight:900;}
            QLineEdit{background:#0e0e12;color:#fff;border:1px solid #30303a;border-radius:7px;padding:9px;}
            QLineEdit:focus{border-color:#ffcf72;}
            QLabel#editCover{background:#07070a;border:1px solid #2a2a33;border-radius:7px;color:#666671;}
            QPushButton{background:#18181f;color:#ddd;border:1px solid #30303a;border-radius:7px;padding:9px 13px;font-size:11px;font-weight:900;}
            QPushButton:hover{border-color:#ffcf72;color:#fff;}
            QPushButton#saveButton{background:#6b1717;color:#fff;border-color:#8f2929;}
        """)

    def reload(self):
        try:
            self.items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError, json.JSONDecodeError):
            self.items = []
        self.list.blockSignals(True)
        self.list.clear()
        for item in self.items:
            title = str(item.get("title") or "(geen titel)")
            artist = str(item.get("artist") or "")
            self.list.addItem(QListWidgetItem(f"{title}\n{artist}" if artist else title))
        self.list.blockSignals(False)
        if self.items:
            self.list.setCurrentRow(min(max(self.current_index, 0), len(self.items) - 1))
        else:
            self.current_index = -1
            self._clear_form()

    def select(self, index):
        if index < 0 or index >= len(self.items):
            return
        self.current_index = index
        data = self.items[index]
        for key, edit in self.fields.items():
            edit.setText(str(data.get(key) or ""))
        self._show_cover(str(data.get("cover") or ""))

    def new_item(self):
        self.items.append({"title":"", "artist":"", "date":"", "location":"", "duration":"", "audio":"", "cover":""})
        self.current_index = len(self.items) - 1
        self._write()

    def choose_cover(self):
        if self.current_index < 0:
            self.new_item()
        path, _ = QFileDialog.getOpenFileName(self, "Kies cover", "", "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:
            return
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        src = Path(path)
        dest = COVERS_DIR / f"liveset_{abs(hash(src.name + str(src.stat().st_mtime_ns)))}{src.suffix.lower()}"
        shutil.copy2(src, dest)
        self.items[self.current_index]["cover"] = str(dest)
        self._show_cover(str(dest))

    def _show_cover(self, path):
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            self.cover.setPixmap(QPixmap())
            self.cover.setText("GEEN COVER")
            return
        size = self.cover.size()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        self.cover.setText("")
        self.cover.setPixmap(scaled.copy(x, y, size.width(), size.height()))

    def save(self):
        if self.current_index < 0:
            return
        cover = self.items[self.current_index].get("cover", "")
        self.items[self.current_index] = {key: edit.text().strip() for key, edit in self.fields.items()}
        self.items[self.current_index]["cover"] = cover
        self._write()

    def delete_current(self):
        if self.current_index < 0:
            return
        self.items.pop(self.current_index)
        self.current_index = min(self.current_index, len(self.items) - 1)
        self._write()

    def _clear_form(self):
        for edit in self.fields.values():
            edit.clear()
        self.cover.setPixmap(QPixmap())
        self.cover.setText("GEEN COVER")

    def _write(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        LIVESETS_FILE.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
        self.changed.emit()
        self.reload()
