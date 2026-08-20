from pathlib import Path

TARGET = Path("gui/mp3_duplicate_cleaner.py")

CODE = r'''from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QCheckBox,
    QProgressBar, QWidget, QScrollArea,
)

from database.database import get_connection

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MP3 = None
    MUTAGEN_AVAILABLE = False

_COPY_SUFFIX_RE = re.compile(r"\s*(?:\([0-9]+\)|\[[0-9]+\]|[_-](?:copy|kopie|[0-9]+))\s*$", re.I)

def norm_text(value):
    value = str(value or "").strip().casefold().replace("_", " ")
    return re.sub(r"\s+", " ", value).strip()

def norm_title(value):
    value = norm_text(value)
    while True:
        cleaned = _COPY_SUFFIX_RE.sub("", value).strip(" -_")
        if cleaned == value:
            return value
        value = cleaned

def track_key(artist, title):
    a = norm_text(artist)
    t = norm_title(title)
    return f"{a}|||{t}" if a and t else ""

def duration_text(path, db_duration):
    try:
        value = float(db_duration)
        if value > 0:
            s = int(round(value))
            return f"{s//60}:{s%60:02d}"
    except Exception:
        pass
    if MUTAGEN_AVAILABLE and Path(path).is_file():
        try:
            s = int(round(float(MP3(path).info.length)))
            return f"{s//60}:{s%60:02d}"
        except Exception:
            pass
    return "--:--"

def ensure_ignore_table():
    conn = get_connection()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS mp3_duplicate_ignored (track_key TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
    finally:
        conn.close()

class ScanWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stop_flag = False
    def stop(self):
        self.stop_flag = True
        self.requestInterruption()
    def run(self):
        try:
            conn = get_connection()
            try:
                rows = conn.execute("""
                    SELECT m.id, m.path, m.artist, m.title, m.album, m.year,
                           m.duration, COALESCE(m.metadata_checked,0),
                           EXISTS(SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id)
                    FROM mp3_files m
                    WHERE m.path IS NOT NULL
                    ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE, m.path COLLATE NOCASE
                """).fetchall()
                ignored = {str(r[0]) for r in conn.execute("SELECT track_key FROM mp3_duplicate_ignored")}
            finally:
                conn.close()
            groups = defaultdict(list)
            total = len(rows)
            for n, row in enumerate(rows, 1):
                if self.stop_flag or self.isInterruptionRequested():
                    return
                mp3_id, path, artist, title, album, year, duration, checked, linked = row
                path = str(path or "")
                if path and Path(path).is_file():
                    key = track_key(artist, title)
                    if key:
                        groups[key].append({
                            "id": int(mp3_id), "path": path,
                            "artist": str(artist or "").strip(),
                            "title": str(title or "").strip(),
                            "album": str(album or "").strip(),
                            "year": year, "duration": duration,
                            "checked": int(checked or 0), "linked": int(linked or 0),
                        })
                if n == total or n % 250 == 0:
                    self.progress.emit(n, total)
            result = []
            for key, files in groups.items():
                if len(files) >= 2:
                    result.append({"track_key": key, "ignored": key in ignored, "files": files})
            result.sort(key=lambda g: (g["ignored"], -len(g["files"]), g["files"][0]["artist"].casefold(), g["files"][0]["title"].casefold()))
            self.finished_scan.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))

class FileRow(QWidget):
    changed = Signal()
    def __init__(self, member, parent=None):
        super().__init__(parent)
        self.member = member
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)
        self.check = QCheckBox()
        self.check.setFixedWidth(28)
        self.check.stateChanged.connect(lambda _=0: self.changed.emit())
        layout.addWidget(self.check)
        text = QLabel()
        text.setWordWrap(True)
        d = duration_text(member["path"], member["duration"])
        status = []
        if member["linked"]: status.append("VINYL")
        if member["checked"]: status.append("META KLAAR")
        suffix = " | " + " / ".join(status) if status else ""
        text.setText(
            f"{Path(member['path']).name} | DUUR {d}{suffix}<br>"
            f"<span style='color:#999'>PAD: {member['path']}</span>"
        )
        layout.addWidget(text, 1)

class GroupRow(QWidget):
    changed = Signal()
    def __init__(self, group, parent=None):
        super().__init__(parent)
        self.group = group
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.check = QCheckBox()
        self.check.setFixedWidth(28)
        self.check.stateChanged.connect(lambda _=0: self.changed.emit())
        layout.addWidget(self.check)
        title = QLabel(f"GROEP | {group['files'][0]['artist']} - {group['files'][0]['title']} | {len(group['files'])} BESTANDEN")
        title.setStyleSheet("font-weight:900;color:#fff;")
        title.setWordWrap(True)
        layout.addWidget(title, 1)

class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MP3 DUBBELE TRACKS")
        self.resize(1200, 820)
        self.worker = None
        self.groups = []
        self.file_checks = []
        self.group_checks = []
        self.show_ignored = False
        self.closing = False
        ensure_ignore_table()
        root = QVBoxLayout(self)
        title = QLabel("MP3 DUBBELE TRACKS")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)
        info = QLabel("Echte vinkvakjes: bestand aanvinken = kandidaat voor verwijderen. Groep aanvinken = groep als GEEN ECHTE DUBBEL negeren. Verwijderen is definitief van de schijf.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#aaaab3;")
        root.addWidget(info)
        self.progress = QProgressBar()
        root.addWidget(self.progress)
        self.summary = QLabel("Nog niet gescand.")
        self.summary.setStyleSheet("color:#d84b91;font-weight:bold;")
        root.addWidget(self.summary)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(4)
        scroll.setWidget(self.container)
        root.addWidget(scroll, 1)
        buttons = QHBoxLayout()
        self.scan_button = QPushButton("SCAN DUBBELS")
        self.delete_button = QPushButton("AANGEVINKTE BESTANDEN VERWIJDEREN")
        self.ignore_button = QPushButton("AANGEVINKTE GROEPEN NEGEREN")
        self.toggle_button = QPushButton("TOON GENEGEERDE")
        self.close_button = QPushButton("SLUITEN")
        self.delete_button.setEnabled(False)
        self.ignore_button.setEnabled(False)
        for b in (self.scan_button,self.delete_button,self.ignore_button,self.toggle_button,self.close_button): buttons.addWidget(b)
        root.addLayout(buttons)
        self.scan_button.clicked.connect(self.scan)
        self.delete_button.clicked.connect(self.delete_checked)
        self.ignore_button.clicked.connect(self.ignore_checked)
        self.toggle_button.clicked.connect(self.toggle_ignored)
        self.close_button.clicked.connect(self.reject)
        self.setStyleSheet("""
            QDialog {background:#0b0b0f;color:#f2f2f5;}
            QScrollArea {background:#0f0f14;border:1px solid #25252d;}
            QCheckBox {spacing:8px;}
            QCheckBox::indicator {width:20px;height:20px;border:2px solid #555;border-radius:4px;background:#15151b;}
            QCheckBox::indicator:checked {background:#d84b91;border-color:#d84b91;}
            QPushButton {background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;}
            QPushButton:hover {border-color:#d84b91;background:#24242c;}
            QLabel {color:#f2f2f5;}
            """)
    def clear_container(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.file_checks.clear(); self.group_checks.clear()
    def scan(self):
        if self.worker and self.worker.isRunning(): return
        self.closing = False
        self.clear_container()
        self.progress.setValue(0)
        self.summary.setText("Scannen van MP3's...")
        self.scan_button.setEnabled(False)
        self.worker = ScanWorker(self)
        self.worker.progress.connect(lambda n,t: self.progress_update(n,t))
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(lambda: self.scan_button.setEnabled(True) if not self.closing else None)
        self.worker.start()
    def progress_update(self,n,t):
        self.progress.setValue(int(n/t*100) if t else 0)
        self.summary.setText(f"Scannen: {n:,} / {t:,} MP3's")
    def on_failed(self,msg):
        if not self.closing: QMessageBox.critical(self,"Dubbel-scan mislukt",msg)
        self.scan_button.setEnabled(True)
    def on_finished(self, groups):
        if self.closing: return
        self.groups = groups or []
        self.clear_container()
        visible = [g for g in self.groups if self.show_ignored or not g["ignored"]]
        if not visible:
            self.summary.setText("Geen zichtbare dubbele groepen.")
            self.progress.setValue(100); return
        for group in visible:
            header = GroupRow(group)
            header.changed.connect(self.update_buttons)
            header.check.setProperty("track_key", group["track_key"])
            self.group_checks.append(header.check)
            self.container_layout.addWidget(header)
            for member in group["files"]:
                row = FileRow(member)
                row.changed.connect(self.update_buttons)
                row.check.setProperty("mp3_id", member["id"])
                row.check.setProperty("path", member["path"])
                row.check.setProperty("linked", member["linked"])
                self.file_checks.append(row.check)
                self.container_layout.addWidget(row)
        self.container_layout.addStretch()
        self.progress.setValue(100)
        count = len(visible)
        files = sum(max(0,len(g["files"])-1) for g in visible)
        self.summary.setText(f"{count:,} groepen zichtbaar | {files:,} overtollige kandidaten")
        self.update_buttons()
    def update_buttons(self):
        deletes = sum(1 for c in self.file_checks if c.isChecked() and not bool(c.property("linked")))
        ignores = sum(1 for c in self.group_checks if c.isChecked())
        self.delete_button.setEnabled(deletes>0)
        self.ignore_button.setEnabled(ignores>0)
        self.delete_button.setText(f"AANGEVINKTE BESTANDEN VERWIJDEREN ({deletes})")
        self.ignore_button.setText(f"AANGEVINKTE GROEPEN NEGEREN ({ignores})")
    def ignore_checked(self):
        keys = [str(c.property("track_key") or "") for c in self.group_checks if c.isChecked()]
        keys = [k for k in keys if k]
        if not keys: return
        conn = get_connection()
        try:
            conn.executemany("INSERT OR IGNORE INTO mp3_duplicate_ignored(track_key) VALUES (?)", [(k,) for k in keys])
            conn.commit()
        finally: conn.close()
        self.scan()
    def toggle_ignored(self):
        self.show_ignored = not self.show_ignored
        self.toggle_button.setText("VERBERG GENEGEERDE" if self.show_ignored else "TOON GENEGEERDE")
        if self.groups: self.on_finished(self.groups)
        else: self.scan()
    def delete_checked(self):
        selected = [c for c in self.file_checks if c.isChecked() and not bool(c.property("linked"))]
        if not selected: return
        paths = [str(c.property("path") or "") for c in selected]
        text = "VERWIJDER DEZE BESTANDEN ECHT VAN DE SCHIJF?\n\n" + "\n".join(paths[:15])
        if len(paths)>15: text += f"\n... en nog {len(paths)-15}..."
        answer = QMessageBox.question(self,"Definitief verwijderen",text,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        errors=[]
        conn=get_connection()
        try:
            for c in selected:
                path=str(c.property("path") or "")
                mp3_id=int(c.property("mp3_id"))
                try:
                    if Path(path).exists(): Path(path).unlink()
                    conn.execute("DELETE FROM mp3_files WHERE id=?",(mp3_id,))
                except Exception as exc: errors.append(f"{path}: {exc}")
            conn.commit()
        finally: conn.close()
        if errors: QMessageBox.warning(self,"Niet alles verwijderd","\n".join(errors[:10]))
        self.scan()
    def closeEvent(self,event):
        self.closing=True
        if self.worker and self.worker.isRunning():
            self.worker.stop(); self.worker.wait()
        self.worker=None
        event.accept()
'''

TARGET.write_text(CODE, encoding='utf-8')
print('OK: gui/mp3_duplicate_cleaner.py volledig vervangen met echte QCheckBox-widgets.')
'''

path = Path("tools/apply/install_mp3_duplicate_cleaner_real_widgets.py")
path.write_text(CODE, encoding="utf-8")
print(f"Installer geschreven: {path}")
