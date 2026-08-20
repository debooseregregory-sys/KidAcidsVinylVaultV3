from pathlib import Path

TARGET = Path("gui/mp3_duplicate_cleaner.py")

CODE = r'''from __future__ import annotations

import re
import sqlite3
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
    re.IGNORECASE,
)


def norm_text(value: str) -> str:
    value = str(value or "").strip().casefold()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def norm_title(value: str) -> str:
    value = norm_text(value)
    while True:
        cleaned = _COPY_SUFFIX_RE.sub("", value).strip(" -_")
        if cleaned == value:
            return value
        value = cleaned


def track_key(artist: str, title: str) -> str:
    artist_n = norm_text(artist)
    title_n = norm_title(title)
    if not artist_n or not title_n:
        return ""
    return f"{artist_n}|||{title_n}"


def display_duration(path: str, db_duration) -> str:
    try:
        value = float(db_duration)
        if value > 0:
            seconds = int(round(value))
            return f"{seconds // 60}:{seconds % 60:02d}"
    except Exception:
        pass

    if MUTAGEN_AVAILABLE and Path(path).is_file():
        try:
            value = float(MP3(path).info.length)
            seconds = int(round(value))
            return f"{seconds // 60}:{seconds % 60:02d}"
        except Exception:
            pass

    return "--:--"


def ensure_ignore_table():
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mp3_duplicate_ignored (
                track_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_requested = False

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
                            SELECT 1
                            FROM track_mp3 tm
                            WHERE tm.mp3_id = m.id
                        )
                    FROM mp3_files m
                    WHERE m.path IS NOT NULL
                    ORDER BY
                        m.artist COLLATE NOCASE,
                        m.title COLLATE NOCASE,
                        m.path COLLATE NOCASE
                    """
                ).fetchall()
            finally:
                conn.close()

            total = len(rows)
            processed = 0
            by_track = defaultdict(list)

            for row in rows:
                if self._stop_requested or self.isInterruptionRequested():
                    return

                mp3_id, path, artist, title, album, year, duration, checked, linked = row
                path = str(path or "")
                if path and Path(path).is_file():
                    key = track_key(artist, title)
                    if key:
                        by_track[key].append(
                            {
                                "id": int(mp3_id),
                                "path": path,
                                "artist": str(artist or "").strip(),
                                "title": str(title or "").strip(),
                                "album": str(album or "").strip(),
                                "year": year,
                                "duration": duration,
                                "checked": int(checked or 0),
                                "linked": int(linked or 0),
                            }
                        )

                processed += 1
                if processed == total or processed % 250 == 0:
                    self.progress.emit(processed, total)

            conn = get_connection()
            try:
                ignored = {
                    str(r[0])
                    for r in conn.execute(
                        "SELECT track_key FROM mp3_duplicate_ignored"
                    ).fetchall()
                }
            finally:
                conn.close()

            groups = []
            for key, members in by_track.items():
                if self._stop_requested or self.isInterruptionRequested():
                    return
                if len(members) < 2:
                    continue
                groups.append(
                    {
                        "track_key": key,
                        "ignored": key in ignored,
                        "files": members,
                    }
                )

            groups.sort(
                key=lambda g: (
                    g["ignored"],
                    -len(g["files"]),
                    g["files"][0]["artist"].casefold(),
                    g["files"][0]["title"].casefold(),
                )
            )

            self.finished_scan.emit(groups)
        except Exception as exc:
            self.failed.emit(str(exc))


class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MP3 DUBBELE TRACKS")
        self.resize(1180, 820)
        self.groups = []
        self.worker = None
        self._closing = False
        self.show_ignored = False

        ensure_ignore_table()

        root = QVBoxLayout(self)
        root.setSpacing(10)

        title = QLabel("MP3 DUBBELE TRACKS")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)

        info = QLabel(
            "Vink een bestand aan om het te verwijderen. "
            "Vink een GROEPSREGEL aan om die volledige trackgroep als GEEN ECHTE DUBBEL te markeren. "
            "Verwijderen is definitief en verwijdert het bestand van de schijf."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#aaaab3;")
        root.addWidget(info)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)

        self.summary = QLabel("Nog niet gescand.")
        self.summary.setStyleSheet("color:#d84b91;font-weight:bold;")
        root.addWidget(self.summary)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list.itemChanged.connect(self.on_item_changed)
        root.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("[ SCAN DUBBELS ]")
        self.delete_button = QPushButton("[ AANGEVINKTE BESTANDEN VERWIJDEREN ]")
        self.ignore_button = QPushButton("[ AANGEVINKTE GROEPEN NEGEREN ]")
        self.show_ignored_button = QPushButton("[ TOON GENEGEERDE ]")
        self.close_button = QPushButton("[ SLUITEN ]")

        self.delete_button.setEnabled(False)
        self.ignore_button.setEnabled(False)

        actions.addWidget(self.scan_button)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.ignore_button)
        actions.addWidget(self.show_ignored_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
        self.delete_button.clicked.connect(self.delete_checked)
        self.ignore_button.clicked.connect(self.ignore_checked_groups)
        self.show_ignored_button.clicked.connect(self.toggle_ignored)
        self.close_button.clicked.connect(self.reject)

        self.setStyleSheet(
            """
            QDialog { background:#0b0b0f; color:#f2f2f5; }
            QListWidget { background:#0f0f14; border:1px solid #25252d; }
            QListWidget::item { padding:8px; border-bottom:1px solid #24242d; }
            QListWidget::item:selected { background:#271522; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a; border-radius:6px; padding:8px 10px; }
            QPushButton:hover { border-color:#d84b91; background:#24242c; }
            QProgressBar { border:1px solid #30303a; background:#18181f; height:12px; border-radius:5px; }
            QProgressBar::chunk { background:#d84b91; border-radius:5px; }
            """
        )

    def scan(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self._closing = False
        self.groups = []
        self.list.clear()
        self.progress.setValue(0)
        self.summary.setText("Scannen van MP3's...")
        self.scan_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.ignore_button.setEnabled(False)

        self.worker = HashWorker(self)
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
        if not self._closing:
            QMessageBox.critical(self, "Dubbel-scan mislukt", message)
        self.scan_button.setEnabled(True)

    def on_worker_finished(self):
        if self.worker is not None and not self.worker.isRunning():
            self.scan_button.setEnabled(True)

    def on_finished(self, groups):
        if self._closing:
            return

        self.groups = groups or []
        self.progress.setValue(100)
        self.list.clear()

        visible = [g for g in self.groups if self.show_ignored or not g["ignored"]]
        ignored_count = sum(1 for g in self.groups if g["ignored"])

        if not visible:
            self.summary.setText(
                f"Geen zichtbare dubbele groepen.  •  {ignored_count} groepen genegeerd."
            )
            self.scan_button.setEnabled(True)
            return

        duplicate_files = sum(max(0, len(g["files"]) - 1) for g in visible)

        for group_index, group in enumerate(visible, 1):
            members = group["files"]
            first = members[0]
            artist = first["artist"] or "Onbekende artiest"
            title = first["title"] or "Onbekende titel"

            header = QListWidgetItem(
                f"GROEP {group_index} | {artist} - {title} | {len(members)} BESTANDEN"
            )
            header.setData(Qt.ItemDataRole.UserRole, {
                "kind": "group",
                "track_key": group["track_key"],
                "ignored": group["ignored"],
            })
            header.setFlags(header.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            header.setCheckState(Qt.CheckState.Unchecked)
            if group["ignored"]:
                header.setText(header.text() + " | GEGENEGEERD")
            self.list.addItem(header)

            for member in members:
                duration = display_duration(member["path"], member["duration"])
                status = []
                if member["linked"]:
                    status.append("VINYL")
                if member["checked"]:
                    status.append("META KLAAR")
                suffix = " | " + " / ".join(status) if status else ""

                label = (
                    f"  {Path(member['path']).name} | DUUR {duration}{suffix}\n"
                    f"    PAD: {member['path']}"
                )

                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, {
                    "kind": "file",
                    "id": member["id"],
                    "path": member["path"],
                    "linked": member["linked"],
                    "track_key": group["track_key"],
                })
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setToolTip(member["path"])
                self.list.addItem(item)

        self.summary.setText(
            f"{len(visible):,} groepen zichtbaar | "
            f"{duplicate_files:,} overtollige kandidaten | "
            f"{ignored_count:,} groepen genegeerd"
        )
        self.scan_button.setEnabled(True)
        self.update_buttons()

    def on_item_changed(self, _item):
        if not self._closing:
            self.update_buttons()

    def update_buttons(self):
        delete_count = 0
        ignore_count = 0
        current_group_has_checked = False

        for i in range(self.list.count()):
            item = self.list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") == "file" and item.checkState() == Qt.CheckState.Checked:
                if not data.get("linked"):
                    delete_count += 1
                current_group_has_checked = True
            elif data.get("kind") == "group" and item.checkState() == Qt.CheckState.Checked:
                ignore_count += 1

        self.delete_button.setEnabled(delete_count > 0)
        self.ignore_button.setEnabled(ignore_count > 0)
        self.delete_button.setText(
            f"[ AANGEVINKTE BESTANDEN VERWIJDEREN ({delete_count}) ]"
        )
        self.ignore_button.setText(
            f"[ AANGEVINKTE GROEPEN NEGEREN ({ignore_count}) ]"
        )

    def checked_files(self):
        result = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") == "file" and item.checkState() == Qt.CheckState.Checked:
                result.append(data)
        return result

    def checked_groups(self):
        result = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") == "group" and item.checkState() == Qt.CheckState.Checked:
                result.append(data)
        return result

    def delete_checked(self):
        files = self.checked_files()
        if not files:
            return

        unprotected = [x for x in files if not x.get("linked")]
        protected = [x for x in files if x.get("linked")]

        if not unprotected:
            QMessageBox.information(
                self,
                "Niets verwijderd",
                "Alle aangevinkte bestanden zijn aan VinylVault gekoppeld en blijven beschermd."
            )
            return

        text = (
            f"Je staat op het punt {len(unprotected)} MP3-bestand(en) ECHT VAN DE SCHIJF TE VERWIJDEREN.\n\n"
            "Dit kan niet automatisch worden teruggedraaid.\n\n"
        )
        text += "\n".join(x["path"] for x in unprotected[:10])
        if len(unprotected) > 10:
            text += f"\n... en nog {len(unprotected) - 10}"

        answer = QMessageBox.question(
            self,
            "Echt van de schijf verwijderen?",
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        errors = []
        conn = get_connection()
        try:
            for data in unprotected:
                path = data["path"]
                try:
                    Path(path).unlink()
                    conn.execute(
                        "DELETE FROM mp3_files WHERE id=?",
                        (int(data["id"]),),
                    )
                except Exception as exc:
                    errors.append(f"{path}: {exc}")
            conn.commit()
        finally:
            conn.close()

        if errors:
            QMessageBox.warning(
                self,
                "Gedeeltelijk verwijderd",
                "Sommige bestanden konden niet worden verwijderd:\n\n" + "\n".join(errors[:10]),
            )

        self.scan()

    def ignore_checked_groups(self):
        groups = self.checked_groups()
        if not groups:
            return

        conn = get_connection()
        try:
            for data in groups:
                conn.execute(
                    "INSERT OR IGNORE INTO mp3_duplicate_ignored(track_key) VALUES(?)",
                    (data["track_key"],),
                )
            conn.commit()
        finally:
            conn.close()

        self.show_ignored = False
        self.scan()

    def toggle_ignored(self):
        self.show_ignored = not self.show_ignored
        self.show_ignored_button.setText(
            "[ VERBERG GENEGEERDE ]" if self.show_ignored else "[ TOON GENEGEERDE ]"
        )
        if self.groups:
            self.on_finished(self.groups)
        else:
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
print(f"OK: {TARGET} vervangen met checkbox/ignore versie.")
'''

p.write_text(CODE, encoding="utf-8-sig")
print(f"OK: {TARGET} vervangen met checkbox/ignore versie.")