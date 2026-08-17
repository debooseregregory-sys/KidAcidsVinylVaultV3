from pathlib import Path

TARGET = Path("gui/mp3_duplicate_cleaner.py")

CODE = r'''from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from database.database import get_connection


_COPY_SUFFIX_RE = re.compile(
    r"\s*(?:\([0-9]+\)|\[[0-9]+\]|[_-](?:copy|kopie|[0-9]+))\s*$",
    re.I,
)


def normalize_text(value: str) -> str:
    value = str(value or "").casefold().strip()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_copy_suffix(value: str) -> str:
    value = normalize_text(value)
    while True:
        cleaned = _COPY_SUFFIX_RE.sub("", value).strip(" -_")
        if cleaned == value:
            return value
        value = cleaned


def track_key(artist: str, title: str) -> str:
    artist_n = normalize_text(artist)
    title_n = normalize_copy_suffix(title)
    if not artist_n or not title_n:
        return ""
    return f"{artist_n}|||{title_n}"


def group_key(members: list[dict]) -> str:
    ids = sorted(int(member["id"]) for member in members)
    raw = "track|" + ",".join(str(x) for x in ids)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_ignore_table() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mp3_duplicate_ignored (
                group_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def load_ignored_keys() -> set[str]:
    ensure_ignore_table()
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT group_key FROM mp3_duplicate_ignored"
        ).fetchall()
        return {str(row[0]) for row in rows}
    finally:
        conn.close()


def save_ignored_keys(keys: set[str]) -> None:
    if not keys:
        return
    ensure_ignore_table()
    conn = get_connection()
    try:
        conn.executemany(
            "INSERT OR IGNORE INTO mp3_duplicate_ignored(group_key) VALUES(?)",
            [(key,) for key in keys],
        )
        conn.commit()
    finally:
        conn.close()


def remove_ignored_keys(keys: set[str]) -> None:
    if not keys:
        return
    ensure_ignore_table()
    conn = get_connection()
    try:
        conn.executemany(
            "DELETE FROM mp3_duplicate_ignored WHERE group_key=?",
            [(key,) for key in keys],
        )
        conn.commit()
    finally:
        conn.close()


class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    def __init__(self, ignored_keys: set[str], show_ignored: bool, parent=None):
        super().__init__(parent)
        self.ignored_keys = set(ignored_keys)
        self.show_ignored = bool(show_ignored)
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

                (
                    mp3_id,
                    path,
                    artist,
                    title,
                    album,
                    year,
                    duration,
                    checked,
                    linked,
                ) = row

                path = str(path or "")
                key = track_key(artist, title)

                if path and key and Path(path).is_file():
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

            groups = []

            for key, members in by_track.items():
                if self._stop_requested or self.isInterruptionRequested():
                    return

                if len(members) < 2:
                    continue

                signature = group_key(members)
                ignored = signature in self.ignored_keys

                if ignored and not self.show_ignored:
                    continue

                groups.append(
                    {
                        "kind": "track",
                        "key": key,
                        "group_key": signature,
                        "ignored": ignored,
                        "files": members,
                    }
                )

            groups.sort(
                key=lambda group: (
                    bool(group.get("ignored")),
                    -len(group["files"]),
                    group["files"][0]["artist"].casefold(),
                    group["files"][0]["title"].casefold(),
                )
            )

            self.finished_scan.emit(groups)

        except Exception as exc:
            self.failed.emit(str(exc))


class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MP3 DUBBELE TRACKS")
        self.resize(1120, 780)
        self.groups = []
        self.worker = None
        self._closing = False
        self.ignored_keys = load_ignored_keys()

        root = QVBoxLayout(self)
        root.setSpacing(10)

        title = QLabel("MP3 DUBBELE TRACKS")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)

        info = QLabel(
            "De scanner zoekt dezelfde artiest + titel en behandelt een kopie zoals "
            "'(1)' als dezelfde track. Remix, Club Mix, Rap Version, Instrumental, "
            "Live, enz. blijven afzonderlijk zichtbaar. Je kunt groepen aanvinken "
            "die volgens jou geen echte dubbele zijn; deze worden daarna bij volgende "
            "scans genegeerd."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#aaaab3;")
        root.addWidget(info)

        tools = QHBoxLayout()

        self.show_ignored = QCheckBox("TOON GENEGEERDE")
        self.show_ignored.setChecked(False)
        tools.addWidget(self.show_ignored)

        self.refresh_button = QPushButton("VERVERS SCAN")
        tools.addWidget(self.refresh_button)
        tools.addStretch()
        root.addLayout(tools)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)

        self.summary = QLabel("Nog niet gescand.")
        self.summary.setStyleSheet("color:#d84b91;font-weight:bold;")
        root.addWidget(self.summary)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        actions = QHBoxLayout()

        self.scan_button = QPushButton("[ SCAN DUBBELS ]")
        self.ignore_button = QPushButton("[ GESELECTEERDE AANVINKEN = NEGEREN ]")
        self.ignore_button.setEnabled(False)
        self.unignore_button = QPushButton("[ GESELECTEERDE NEGEREN OPHEFFEN ]")
        self.unignore_button.setEnabled(False)
        self.delete_button = QPushButton("[ GESELECTEERD BESTAND VERWIJDEREN ]")
        self.delete_button.setEnabled(False)
        self.close_button = QPushButton("[ SLUITEN ]")

        actions.addWidget(self.scan_button)
        actions.addWidget(self.ignore_button)
        actions.addWidget(self.unignore_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
        self.refresh_button.clicked.connect(self.scan)
        self.ignore_button.clicked.connect(self.ignore_checked_groups)
        self.unignore_button.clicked.connect(self.unignore_checked_groups)
        self.delete_button.clicked.connect(self.delete_selected_file)
        self.close_button.clicked.connect(self.reject)
        self.show_ignored.toggled.connect(self.scan)
        self.list.itemSelectionChanged.connect(self.on_selection_changed)
        self.list.itemChanged.connect(self.on_item_changed)

        self.setStyleSheet(
            """
            QDialog { background:#0b0b0f; color:#f2f2f5; }
            QListWidget { background:#0f0f14; border:1px solid #25252d; }
            QListWidget::item { padding:9px; border-bottom:1px solid #24242d; }
            QListWidget::item:selected { background:#271522; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a; border-radius:6px; padding:9px 12px; }
            QPushButton:hover { border-color:#d84b91; background:#24242c; }
            QCheckBox { color:#fff; padding:4px; }
            QProgressBar { border:1px solid #30303a; background:#18181f; height:12px; border-radius:5px; }
            QProgressBar::chunk { background:#d84b91; border-radius:5px; }
            """
        )

        self.scan()

    def scan(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self._closing = False
        self.list.clear()
        self.groups = []
        self.progress.setValue(0)
        self.summary.setText("Scannen van MP3's...")
        self.scan_button.setEnabled(False)
        self.ignore_button.setEnabled(False)
        self.unignore_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.worker = HashWorker(
            self.ignored_keys,
            self.show_ignored.isChecked(),
            self,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_progress(self, processed, total):
        value = int((processed / total) * 100) if total else 0
        self.progress.setValue(value)
        self.summary.setText(
            f"Scannen: {processed:,} / {total:,} MP3's"
        )

    def on_worker_finished(self):
        if self.worker is not None and not self.worker.isRunning():
            self.scan_button.setEnabled(True)

    def on_failed(self, message):
        if not self._closing:
            self.scan_button.setEnabled(True)
            QMessageBox.critical(
                self,
                "Dubbel-scan mislukt",
                message,
            )

    def on_finished(self, groups):
        if self._closing:
            return

        self.groups = groups or []
        self.progress.setValue(100)
        self.scan_button.setEnabled(True)
        self.list.clear()

        if not self.groups:
            if self.show_ignored.isChecked():
                self.summary.setText("Geen dubbele groepen gevonden.")
            else:
                ignored = len(self.ignored_keys)
                self.summary.setText(
                    f"Geen nieuwe dubbele groepen gevonden. "
                    f"{ignored:,} groepen zijn genegeerd."
                )
            return

        total_groups = len(self.groups)
        total_files = sum(max(0, len(g["files"]) - 1) for g in self.groups)
        ignored_groups = sum(1 for g in self.groups if g.get("ignored"))

        for group_index, group in enumerate(self.groups, 1):
            members = group["files"]
            first = members[0]
            artist = first["artist"] or "ONBEKENDE ARTIEST"
            title = first["title"] or "ONBEKENDE TITEL"
            ignored = bool(group.get("ignored"))

            header = QListWidgetItem(
                f"GROEP {group_index} - {artist} - {title} - "
                f"{len(members)} BESTANDEN"
            )
            header.setFlags(
                header.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            header.setCheckState(Qt.CheckState.Checked if ignored else Qt.CheckState.Unchecked)
            header.setData(Qt.ItemDataRole.UserRole, {
                "kind": "group",
                "group_key": group["group_key"],
                "ignored": ignored,
            })
            if ignored:
                header.setText(header.text() + " - GENEGEERD")
            self.list.addItem(header)

            for member_index, member in enumerate(members):
                duration = member.get("duration")
                try:
                    duration_text = f"{float(duration):.0f} sec" if duration is not None else "duur onbekend"
                except (TypeError, ValueError):
                    duration_text = "duur onbekend"

                flags = []
                if member["linked"]:
                    flags.append("VINYL GEKOPPELD")
                if member["checked"]:
                    flags.append("METADATA KLAAR")
                if member_index == 0:
                    flags.append("EERSTE KOPIE")

                label = (
                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "
                    f"{Path(member['path']).name} - {duration_text}"
                )
                if flags:
                    label += " - [" + " | ".join(flags) + "]"

                item = QListWidgetItem(label)
                item.setToolTip(
                    "Path: " + member["path"]
                    + "\nArtist: " + member["artist"]
                    + "\nTitle: " + member["title"]
                    + "\nAlbum: " + member["album"]
                    + "\nDuration: " + duration_text
                )
                item.setData(Qt.ItemDataRole.UserRole, {
                    "kind": "file",
                    "group_key": group["group_key"],
                    "path": member["path"],
                    "id": member["id"],
                    "linked": member["linked"],
                })
                self.list.addItem(item)

        self.summary.setText(
            f"{total_groups:,} dubbele groepen - "
            f"{total_files:,} overtollige kopieën - "
            f"{ignored_groups:,} genegeerd"
        )

    def on_selection_changed(self):
        item = self.list.currentItem()
        data = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.delete_button.setEnabled(
            bool(data and data.get("kind") == "file" and not data.get("linked"))
        )
        self.update_group_buttons()

    def on_item_changed(self, _item):
        self.update_group_buttons()

    def update_group_buttons(self):
        checked_groups = []
        unchecked_ignored_groups = []

        for index in range(self.list.count()):
            item = self.list.item(index)
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data or data.get("kind") != "group":
                continue
            checked = item.checkState() == Qt.CheckState.Checked
            ignored = bool(data.get("ignored"))
            if checked and not ignored:
                checked_groups.append(item)
            if not checked and ignored:
                unchecked_ignored_groups.append(item)

        self.ignore_button.setEnabled(bool(checked_groups))
        self.unignore_button.setEnabled(bool(unchecked_ignored_groups))

    def _checked_group_keys(self, want_ignored: bool):
        keys = set()
        for index in range(self.list.count()):
            item = self.list.item(index)
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data or data.get("kind") != "group":
                continue
            checked = item.checkState() == Qt.CheckState.Checked
            ignored = bool(data.get("ignored"))
            if want_ignored:
                if checked and not ignored:
                    keys.add(str(data.get("group_key")))
            else:
                if not checked and ignored:
                    keys.add(str(data.get("group_key")))
        return {key for key in keys if key}

    def ignore_checked_groups(self):
        keys = self._checked_group_keys(True)
        if not keys:
            return

        save_ignored_keys(keys)
        self.ignored_keys.update(keys)
        self.scan()

    def unignore_checked_groups(self):
        keys = self._checked_group_keys(False)
        if not keys:
            return

        remove_ignored_keys(keys)
        self.ignored_keys.difference_update(keys)
        self.scan()

    def delete_selected_file(self):
        item = self.list.currentItem()
        data = item.data(Qt.ItemDataRole.UserRole) if item else None

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
            f"Verwijder dit MP3-bestand?\n\n{path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            Path(path).unlink()
            conn = get_connection()
            try:
                conn.execute(
                    "DELETE FROM mp3_files WHERE id=?",
                    (mp3_id,),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Verwijderen mislukt",
                str(exc),
            )
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
print(f"OK: {TARGET} vervangen met duplicate cleaner met persistent ignore-systeem.")
