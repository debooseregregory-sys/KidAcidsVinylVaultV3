from pathlib import Path

TARGET = Path("gui/mp3_duplicate_cleaner.py")

CODE = r'''from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QCheckBox,
    QProgressBar,
)

from database.database import get_connection

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MP3 = None
    MUTAGEN_AVAILABLE = False

_COPY_SUFFIX_RE = re.compile(
    r"\s*(?:\([0-9]+\)|\[[0-9]+\]|[_-](?:copy|kopie|[0-9]+))\s*$",
    re.I,
)


def ensure_ignore_table():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mp3_duplicate_ignored (
                track_key TEXT PRIMARY KEY,
                artist TEXT,
                title TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def norm(value: str) -> str:
    value = str(value or "").casefold().strip()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def copy_suffix_normalized(value: str) -> str:
    value = norm(value)
    while True:
        cleaned = _COPY_SUFFIX_RE.sub("", value).strip(" -_")
        if cleaned == value:
            return value
        value = cleaned


def track_key(artist: str, title: str) -> str:
    artist_n = norm(artist)
    title_n = copy_suffix_normalized(title)
    if not artist_n or not title_n:
        return ""
    return f"{artist_n}|||{title_n}"


def format_duration(value) -> str:
    try:
        seconds = float(value)
        if seconds <= 0:
            raise ValueError
        total = int(round(seconds))
        minutes, secs = divmod(total, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    except Exception:
        return "--:--"


def duration_for(path: str, stored) -> float | None:
    try:
        if stored is not None and float(stored) > 0:
            return float(stored)
    except Exception:
        pass

    if MUTAGEN_AVAILABLE and Path(path).is_file():
        try:
            return float(MP3(path).info.length)
        except Exception:
            pass

    return None


class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    def __init__(self, ignored_keys=None, parent=None):
        super().__init__(parent)
        self._stop_requested = False
        self.ignored_keys = set(ignored_keys or [])

    def request_stop(self):
        self._stop_requested = True
        self.requestInterruption()

    def run(self):
        try:
            conn = get_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT
                        m.id,
                        m.path,
                        m.artist,
                        m.title,
                        m.album,
                        m.year,
                        m.duration,
                        COALESCE(m.metadata_checked, 0),
                        EXISTS(
                            SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id = m.id
                        )
                    FROM mp3_files m
                    WHERE m.path IS NOT NULL
                    ORDER BY m.artist COLLATE NOCASE,
                             m.title COLLATE NOCASE,
                             m.path COLLATE NOCASE
                    """
                ).fetchall()
            finally:
                conn.close()

            total = len(rows)
            processed = 0
            groups = defaultdict(list)

            for row in rows:
                if self._stop_requested or self.isInterruptionRequested():
                    return

                mp3_id, path, artist, title, album, year, stored_duration, checked, linked = row
                path = str(path or "")
                if not path or not Path(path).is_file():
                    processed += 1
                    if processed == total or processed % 250 == 0:
                        self.progress.emit(processed, total)
                    continue

                key = track_key(artist, title)
                if key and key not in self.ignored_keys:
                    groups[key].append(
                        {
                            "id": int(mp3_id),
                            "path": path,
                            "artist": str(artist or "").strip(),
                            "title": str(title or "").strip(),
                            "album": str(album or "").strip(),
                            "year": year,
                            "duration": duration_for(path, stored_duration),
                            "checked": int(checked or 0),
                            "linked": int(linked or 0),
                        }
                    )

                processed += 1
                if processed == total or processed % 250 == 0:
                    self.progress.emit(processed, total)

            result = []
            for key, members in groups.items():
                if len(members) < 2:
                    continue
                members.sort(key=lambda item: (item["linked"], item["path"].casefold()))
                result.append(
                    {
                        "kind": "track",
                        "key": key,
                        "files": members,
                        "artist": members[0]["artist"],
                        "title": members[0]["title"],
                    }
                )

            result.sort(
                key=lambda group: (
                    -len(group["files"]),
                    group["artist"].casefold(),
                    group["title"].casefold(),
                )
            )

            self.finished_scan.emit(result)

        except Exception as exc:
            self.failed.emit(str(exc))


class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_ignore_table()
        self.setWindowTitle("MP3 DUBBELE TRACKS")
        self.resize(1180, 800)
        self.groups = []
        self.worker = None
        self._closing = False
        self.show_ignored = False

        root = QVBoxLayout(self)
        root.setSpacing(10)

        title = QLabel("MP3 DUBBELE TRACKS")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)

        info = QLabel(
            "Zelfde artiest + titel = mogelijke dubbele track. Kopieen zoals (1) worden samengevoegd. "
            "Versies zoals Remix, Club Mix, Rap Version, Instrumental enz. blijven afzonderlijk. "
            "Per bestand zie je speelduur en het volledige pad."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#aaaab3;")
        root.addWidget(info)

        self.progress = QProgressBar()
        root.addWidget(self.progress)

        self.summary = QLabel("Nog niet gescand.")
        self.summary.setStyleSheet("color:#d84b91;font-weight:bold;")
        root.addWidget(self.summary)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("[ SCAN DUBBELS ]")
        self.ignore_button = QPushButton("[ GESELECTEERDE GROEP NEGEREN ]")
        self.show_ignored_button = QPushButton("[ GENEGEERDE TONEN ]")
        self.unignore_button = QPushButton("[ NEGEREN OPHEFFEN ]")
        self.delete_button = QPushButton("[ VERWIJDER GESELECTEERDE MP3 ]")
        self.close_button = QPushButton("[ SLUITEN ]")

        self.ignore_button.setEnabled(False)
        self.unignore_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        actions.addWidget(self.scan_button)
        actions.addWidget(self.ignore_button)
        actions.addWidget(self.show_ignored_button)
        actions.addWidget(self.unignore_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
        self.ignore_button.clicked.connect(self.ignore_selected_group)
        self.show_ignored_button.clicked.connect(self.toggle_ignored)
        self.unignore_button.clicked.connect(self.unignore_selected_group)
        self.delete_button.clicked.connect(self.delete_selected)
        self.close_button.clicked.connect(self.reject)
        self.list.itemSelectionChanged.connect(self.on_selection_changed)

        self.setStyleSheet(
            """
            QDialog { background:#0b0b0f; color:#f2f2f5; }
            QListWidget { background:#0f0f14; border:1px solid #25252d; }
            QListWidget::item { padding:10px; border-bottom:1px solid #24242d; }
            QListWidget::item:selected { background:#271522; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a; border-radius:6px; padding:9px 12px; }
            QPushButton:hover { border-color:#d84b91; background:#24242c; }
            QProgressBar { border:1px solid #30303a; background:#18181f; height:12px; border-radius:5px; }
            QProgressBar::chunk { background:#d84b91; border-radius:5px; }
            """
        )

    def ignored_keys(self):
        conn = get_connection()
        try:
            return {
                str(row[0])
                for row in conn.execute(
                    "SELECT track_key FROM mp3_duplicate_ignored"
                ).fetchall()
            }
        finally:
            conn.close()

    def scan(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self._closing = False
        self.list.clear()
        self.progress.setValue(0)
        self.summary.setText("Scannen van MP3's...")
        self.scan_button.setEnabled(False)

        self.worker = HashWorker(self.ignored_keys(), self)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_progress(self, processed, total):
        value = int((processed / total) * 100) if total else 0
        self.progress.setValue(value)
        self.summary.setText(f"Scannen: {processed:,} / {total:,} MP3's")

    def on_failed(self, message):
        self.scan_button.setEnabled(True)
        if not self._closing:
            QMessageBox.critical(self, "Dubbel-scan mislukt", message)

    def on_worker_finished(self):
        if not self._closing:
            self.scan_button.setEnabled(True)

    def on_finished(self, groups):
        if self._closing:
            return

        self.groups = groups or []
        self.progress.setValue(100)
        self.list.clear()
        self.scan_button.setEnabled(True)

        if not self.groups:
            self.summary.setText(
                "Geen dubbele tracks gevonden (genegeerde groepen zijn verborgen)."
            )
            return

        duplicate_files = sum(max(0, len(group["files"]) - 1) for group in self.groups)

        for group_index, group in enumerate(self.groups, 1):
            members = group["files"]
            artist = group["artist"] or "Onbekende artiest"
            title = group["title"] or "Onbekende titel"

            header = QListWidgetItem(
                f"GROEP {group_index} | {artist} - {title} | {len(members)} BESTANDEN"
            )
            header.setData(
                Qt.ItemDataRole.UserRole,
                {"kind": "header", "group": group_index - 1},
            )
            self.list.addItem(header)

            for member_index, member in enumerate(members):
                flags = []
                if member["linked"]:
                    flags.append("VINYL GEKOPPELD")
                if member["checked"]:
                    flags.append("METADATA KLAAR")

                text = (
                    f"{Path(member['path']).name}"
                    f" | DUUR {format_duration(member['duration'])}"
                )
                if flags:
                    text += " | " + " | ".join(flags)

                item = QListWidgetItem(text)
                item.setToolTip(member["path"])
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "kind": "file",
                        "group": group_index - 1,
                        "member": member_index,
                        "path": member["path"],
                        "id": member["id"],
                        "linked": member["linked"],
                    },
                )
                self.list.addItem(item)

                path_item = QListWidgetItem(
                    f"    PAD: {member['path']}"
                )
                path_item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "kind": "path",
                        "group": group_index - 1,
                        "member": member_index,
                    },
                )
                self.list.addItem(path_item)

        self.summary.setText(
            f"{len(self.groups):,} dubbele groepen | {duplicate_files:,} overtollige kopieen"
        )

    def selected_group_index(self):
        selected = self.list.currentItem()
        data = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        if not data:
            return None
        return data.get("group")

    def on_selection_changed(self):
        group_index = self.selected_group_index()
        selected = self.list.currentItem()
        data = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        self.ignore_button.setEnabled(group_index is not None and not self.show_ignored)
        self.unignore_button.setEnabled(group_index is not None and self.show_ignored)
        self.delete_button.setEnabled(
            bool(data and data.get("kind") == "file" and not data.get("linked"))
        )

    def ignore_selected_group(self):
        group_index = self.selected_group_index()
        if group_index is None or group_index >= len(self.groups):
            return

        group = self.groups[group_index]
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO mp3_duplicate_ignored(track_key, artist, title) VALUES (?, ?, ?)",
                (group["key"], group["artist"], group["title"]),
            )
            conn.commit()
        finally:
            conn.close()

        self.scan()

    def toggle_ignored(self):
        self.show_ignored = not self.show_ignored
        if self.show_ignored:
            self.show_ignored_button.setText("[ NORMALE TONEN ]")
            self.load_ignored()
        else:
            self.show_ignored_button.setText("[ GENEGEERDE TONEN ]")
            self.scan()

    def load_ignored(self):
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT track_key, artist, title FROM mp3_duplicate_ignored ORDER BY artist, title"
            ).fetchall()
        finally:
            conn.close()

        self.groups = [
            {
                "kind": "ignored",
                "key": str(row[0]),
                "artist": str(row[1] or ""),
                "title": str(row[2] or ""),
                "files": [],
            }
            for row in rows
        ]

        self.list.clear()
        for index, group in enumerate(self.groups, 1):
            item = QListWidgetItem(
                f"GENEGEERD {index} | {group['artist']} - {group['title']}"
            )
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"kind": "header", "group": index - 1},
            )
            self.list.addItem(item)

        self.summary.setText(
            f"{len(self.groups):,} genegeerde groepen"
        )

    def unignore_selected_group(self):
        group_index = self.selected_group_index()
        if group_index is None or group_index >= len(self.groups):
            return

        key = self.groups[group_index]["key"]
        conn = get_connection()
        try:
            conn.execute(
                "DELETE FROM mp3_duplicate_ignored WHERE track_key=?",
                (key,),
            )
            conn.commit()
        finally:
            conn.close()

        self.load_ignored()

    def delete_selected(self):
        selected = self.list.currentItem()
        data = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        if not data or data.get("kind") != "file":
            return

        if data.get("linked"):
            QMessageBox.warning(
                self,
                "Beschermd bestand",
                "Dit MP3-bestand is aan een VinylVault-track gekoppeld en wordt niet verwijderd.",
            )
            return

        path = str(data.get("path") or "")
        mp3_id = int(data.get("id"))
        answer = QMessageBox.question(
            self,
            "Dubbele MP3 verwijderen",
            f"Verwijder deze MP3?\n\n{path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            Path(path).unlink()
            conn = get_connection()
            try:
                conn.execute("DELETE FROM mp3_files WHERE id=?", (mp3_id,))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            QMessageBox.critical(self, "Verwijderen mislukt", str(exc))
            return

        self.scan()

    def closeEvent(self, event):
        self._closing = True
        worker = self.worker
        if worker is not None and worker.isRunning():
            worker.request_stop()
            worker.wait()
        self.worker = None
        event.accept()
'''

TARGET.write_text(CODE, encoding="utf-8-sig")
print(f"OK: {TARGET} vervangen met duplicate cleaner met pad + speelduur.")
'''

Path("tools/apply/replace_mp3_duplicate_cleaner_with_details.py").write_text(CODE, encoding="utf-8-sig")
print("Fixer geschreven.")
