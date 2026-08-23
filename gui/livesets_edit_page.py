from __future__ import annotations
from gui.app_settings import confirm_delete

import json
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

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
        self._building = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._restore_save_button)
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
        for key, label in [
            ("title", "Titel"), ("artist", "Artiest / DJ"), ("date", "Datum"),
            ("location", "Locatie"), ("duration", "Duur / tracks"), ("audio", "Audio bestand"),
        ]:
            lab = QLabel(label.upper())
            lab.setObjectName("fieldLabel")
            form.addWidget(lab)
            if key == "audio":
                audio_row = QHBoxLayout()
                audio_row.setSpacing(6)
                edit = QLineEdit()
                self.fields[key] = edit
                audio_row.addWidget(edit, 1)
                choose_audio = QPushButton("KIES AUDIO")
                choose_audio.setObjectName("audioButton")
                choose_audio.clicked.connect(self.choose_audio)
                audio_row.addWidget(choose_audio)
                form.addLayout(audio_row)
            else:
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
        delete.setObjectName("deleteButton")
        delete.clicked.connect(self.delete_current)
        self.save_button = QPushButton("OPSLAAN")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.save)
        actions.addWidget(new_btn)
        actions.addStretch(1)
        actions.addWidget(delete)
        actions.addWidget(self.save_button)
        form.addLayout(actions)

        self.save_status = QLabel("")
        self.save_status.setObjectName("saveStatus")
        self.save_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.addWidget(self.save_status)

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
            QLabel#saveStatus{color:#69d391;font-size:10px;font-weight:900;min-height:18px;}
            QPushButton{background:#18181f;color:#ddd;border:1px solid #30303a;border-radius:7px;padding:9px 13px;font-size:11px;font-weight:900;}
            QPushButton:hover{border-color:#ffcf72;color:#fff;}
            QPushButton#audioButton{background:#24242c;color:#fff;border-color:#4a4a56;}
            QPushButton#audioButton:hover{background:#30303a;border-color:#ffcf72;color:#fff;}
            QPushButton#saveButton{background:#6b1717;color:#fff;border-color:#8f2929;}
            QPushButton#saveButton:hover{background:#852020;border-color:#b23a3a;color:#fff;}
            QPushButton#saveButton[saved="true"]{background:#267344;color:#fff;border-color:#43a863;}
            QPushButton#deleteButton{background:#35161b;color:#ffb5bd;border-color:#6d2731;}
            QPushButton#deleteButton:hover{background:#4a1b22;border-color:#a43b49;color:#fff;}
        """)

    def reload(self):
        try:
            self.items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
            if not isinstance(self.items, list): self.items = []
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
            self.current_index = min(max(self.current_index, 0), len(self.items) - 1)
            self.list.setCurrentRow(self.current_index)
            self.select(self.current_index)
        else:
            self.current_index = -1
            self._clear_form()

    def select(self, index):
        if self._building or index < 0 or index >= len(self.items): return
        self.current_index = index
        data = self.items[index]
        for key, edit in self.fields.items(): edit.setText(str(data.get(key) or ""))
        self._show_cover(str(data.get("cover") or ""))
        self._clear_save_feedback()

    def new_item(self):
        if self.current_index >= 0: self._collect_form()
        self.items.append({"title":"","artist":"","date":"","location":"","duration":"","audio":"","cover":""})
        self.current_index = len(self.items) - 1
        self._write(reload_after=False)
        self.reload()

    def choose_audio(self):
        if self.current_index < 0: self.new_item()
        path, _ = QFileDialog.getOpenFileName(self, "Kies liveset audio", "", "Audio bestanden (*.mp3 *.wav *.flac *.m4a *.aac *.ogg);;Alle bestanden (*.*)")
        if not path: return
        self.fields["audio"].setText(path)
        self.save(show_message=False)

    def choose_cover(self):
        if self.current_index < 0: self.new_item()
        path, _ = QFileDialog.getOpenFileName(self, "Kies cover", "", "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path: return
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        src = Path(path)
        try: stamp = src.stat().st_mtime_ns
        except OSError: stamp = 0
        dest = COVERS_DIR / f"liveset_{abs(hash(src.name + str(stamp)))}{src.suffix.lower()}"
        try: shutil.copy2(src, dest)
        except OSError as exc:
            QMessageBox.critical(self, "Cover kopiëren mislukt", f"De cover kon niet worden gekopieerd.\n\n{exc}")
            return
        old_cover = str(self.items[self.current_index].get("cover") or "").strip()
        self.items[self.current_index]["cover"] = str(dest)
        self._show_cover(str(dest))
        if old_cover and Path(old_cover) != dest: self._delete_cover_file(old_cover)
        self._write()

    def _show_cover(self, path):
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            self.cover.setPixmap(QPixmap()); self.cover.setText("GEEN COVER"); return
        size = self.cover.size()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        self.cover.setText("")
        self.cover.setPixmap(scaled.copy(x, y, size.width(), size.height()))

    def _collect_form(self):
        if self.current_index < 0 or self.current_index >= len(self.items): return False
        cover = self.items[self.current_index].get("cover", "")
        self.items[self.current_index] = {key: edit.text().strip() for key, edit in self.fields.items()}
        self.items[self.current_index]["cover"] = cover
        return True

    def save(self, show_message=True):
        if not self._collect_form():
            if show_message: QMessageBox.warning(self, "Opslaan", "Selecteer eerst een liveset.")
            return False
        if not self._write(reload_after=False): return False
        row = self.current_index
        item = self.items[row]
        title = str(item.get("title") or "(geen titel)")
        artist = str(item.get("artist") or "")
        list_item = self.list.item(row)
        if list_item is not None: list_item.setText(f"{title}\n{artist}" if artist else title)
        self.changed.emit()
        self._show_save_feedback()
        if show_message: QMessageBox.information(self, "Liveset opgeslagen", "De liveset is opgeslagen.")
        return True

    def _show_save_feedback(self):
        self._save_timer.stop()
        self.save_button.setText("OPGESLAGEN ✓")
        self.save_button.setProperty("saved", "true")
        self.save_button.style().unpolish(self.save_button)
        self.save_button.style().polish(self.save_button)
        self.save_status.setText("✓ Liveset opgeslagen")
        self._save_timer.start(1800)

    def _restore_save_button(self):
        self.save_button.setText("OPSLAAN")
        self.save_button.setProperty("saved", "false")
        self.save_button.style().unpolish(self.save_button)
        self.save_button.style().polish(self.save_button)
        self.save_status.clear()

    def _clear_save_feedback(self):
        if self._save_timer.isActive(): self._save_timer.stop()
        if hasattr(self, "save_button"):
            self.save_button.setText("OPSLAAN")
            self.save_button.setProperty("saved", "false")
            self.save_button.style().unpolish(self.save_button)
            self.save_button.style().polish(self.save_button)
        if hasattr(self, "save_status"): self.save_status.clear()

    @staticmethod
    def _delete_cover_file(path):
        if not path: return
        try:
            cover_path = Path(path)
            if not cover_path.exists() or not cover_path.is_file(): return
            if cover_path.parent.resolve() != COVERS_DIR.resolve(): return
            cover_path.unlink()
        except OSError: pass

    def delete_current(self):
        if self.current_index < 0 or self.current_index >= len(self.items): return
        item = self.items[self.current_index]
        title = str(item.get("title") or "(geen titel)")
        artist = str(item.get("artist") or "")
        description = f"Weet je zeker dat je deze liveset wilt verwijderen?\n\n{title}"
        if artist: description += f"\n{artist}"
        description += "\n\nDe liveset en de bijbehorende cover worden verwijderd. Het MP3/audio-bestand blijft behouden."
        answer = QMessageBox.question(self, "Liveset verwijderen", description, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        cover_path = str(item.get("cover") or "").strip()
        self.items.pop(self.current_index)
        self.current_index = min(self.current_index, len(self.items) - 1)
        self._delete_cover_file(cover_path)
        self._write()

    def _clear_form(self):
        for edit in self.fields.values(): edit.clear()
        self.cover.setPixmap(QPixmap()); self.cover.setText("GEEN COVER")
        self._clear_save_feedback()

    def _write(self, reload_after=True):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp_file = LIVESETS_FILE.with_suffix(".json.tmp")
        try:
            temp_file.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_file.replace(LIVESETS_FILE)
        except (OSError, TypeError, ValueError) as exc:
            try:
                if temp_file.exists(): temp_file.unlink()
            except OSError: pass
            QMessageBox.critical(self, "Opslaan mislukt", f"De liveset kon niet worden opgeslagen.\n\n{exc}")
            return False
        if reload_after: self.reload()
        return True
