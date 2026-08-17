from __future__ import annotations

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
    QProgressBar,
    QCheckBox,
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


def format_duration(value) -> str:
    try:
        seconds = float(value)
        if seconds > 0:
            seconds = int(round(seconds))
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


def load_ignored_keys():
    ensure_ignore_table()
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


def save_ignored_keys(keys):
    ensure_ignore_table()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM mp3_duplicate_ignored")
        conn.executemany(
            "INSERT OR IGNORE INTO mp3_duplicate_ignored(track_key) VALUES (?)",
            [(key,) for key in sorted(keys)],
        )
        conn.commit()
    finally:
        conn.close()


class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    def __init__(self, ignored_keys=None, show_ignored=False, parent=None):
        super().__init__(parent)
        self.ignored_keys = set(ignored_keys or set())
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
            by_track = defaultdict(list)

            for processed, row in enumerate(rows, 1):
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
                if not path:
                    continue

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

                if processed == total or processed % 250 == 0:
                    self.progress.emit(processed, total)

            groups = []
            for key, members in by_track.items():
                if self._stop_requested or self.isInterruptionRequested():
                    return
                if len(members) < 2:
                    continue

                ignored = key in self.ignored_keys
                if ignored and not self.show_ignored:
                    continue

                groups.append(
                    {
                        "kind": "track",
                        "key": key,
                        "ignored": ignored,
                        "files": members,
                    }
                )

            groups.sort(
                key=lambda group: (
                    group["ignored"],
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
        self.resize(1150, 800)
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
            "Ctrl + klik en Shift + klik werken voor meerdere selecties. "
            "Selecteer een of meer MP3-bestanden om ze te verwijderen. "
            "Selecteer een of meer groepsregels om ze te negeren. "
            "Remix, Club Mix, Rap Version, Instrumental en Live blijven als aparte titels bestaan."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#aaaab3;")
        root.addWidget(info)

        tools = QHBoxLayout()
        self.show_ignored = QCheckBox("TOON GENEGEERDE GROEPEN")
        tools.addWidget(self.show_ignored)
        tools.addStretch()
        root.addLayout(tools)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        root.addWidget(self.progress)

        self.summary = QLabel("Nog niet gescand.")
        self.summary.setStyleSheet("color:#d84b91;font-weight:bold;")
        root.addWidget(self.summary)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        root.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("[ SCAN DUBBELS ]")
        self.ignore_button = QPushButton("[ GESELECTEERDE GROEPEN NEGEREN ]")
        self.unignore_button = QPushButton("[ NEGEREN OPHEFFEN ]")
        self.delete_button = QPushButton("[ GESELECTEERDE BESTANDEN VERWIJDEREN ]")
        self.close_button = QPushButton("[ SLUITEN ]")

        self.ignore_button.setEnabled(False)
        self.unignore_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        actions.addWidget(self.scan_button)
        actions.addWidget(self.ignore_button)
        actions.addWidget(self.unignore_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
        self.show_ignored.toggled.connect(self.scan)
        self.ignore_button.clicked.connect(self.ignore_selected_groups)
        self.unignore_button.clicked.connect(self.unignore_selected_groups)
        self.delete_button.clicked.connect(self.delete_selected_files)
        self.close_button.clicked.connect(self.close)
        self.list.itemSelectionChanged.connect(self.refresh_button_state)

        self.setStyleSheet(
            """
            QDialog { background:#0b0b0f; color:#f2f2f5; }
            QListWidget { background:#0f0f14; border:1px solid #25252d; }
            QListWidget::item { padding:10px; border-bottom:1px solid #24242d; }
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
        self.groups = []
        self.list.clear()
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
        self.summary.setText(f"Scannen: {processed:,} / {total:,} MP3's")

    def on_failed(self, message):
        self.scan_button.setEnabled(True)
        if not self._closing:
            QMessageBox.critical(self, "Dubbel-scan mislukt", message)

    def on_worker_finished(self):
        if self.worker is not None and not self.worker.isRunning():
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
                f"Geen zichtbare dubbele groepen. {len(self.ignored_keys):,} groepen genegeerd."
            )
            self.refresh_button_state()
            return

        duplicate_files = sum(
            max(0, len(group["files"]) - 1)
            for group in self.groups
        )

        for group_index, group in enumerate(self.groups, 1):
            members = group["files"]
            first = members[0]
            artist = first["artist"] or "Onbekende artiest"
            title = first["title"] or "Onbekende titel"
            ignored = bool(group.get("ignored"))

            header = QListWidgetItem(
                f"GROEP {group_index} - {artist} - {title} - {len(members)} BESTANDEN"
            )
            header.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "kind": "group",
                    "group_key": group["key"],
                    "ignored": ignored,
                },
            )
            self.list.addItem(header)

            for member_index, member in enumerate(members):
                duration_text = format_duration(member["duration"])
                flags = []
                if member["linked"]:
                    flags.append("VINYL GEKOPPELD")
                if member["checked"]:
                    flags.append("METADATA KLAAR")
                if member_index == 0:
                    flags.append("EERSTE KOPIE")

                label = (
                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "
                    f"{Path(member['path']).name} | DUUR {duration_text}"
                )
                if flags:
                    label += " | " + " / ".join(flags)

                item = QListWidgetItem(label)
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "kind": "file",
                        "group_key": group["key"],
                        "path": member["path"],
                        "id": member["id"],
                        "linked": bool(member["linked"]),
                    },
                )
                item.setToolTip(
                    "PAD: " + str(member["path"])
                    + "\nDUUR: " + duration_text
                    + "\nARTIST: " + str(member["artist"] or "")
                    + "\nTITEL: " + str(member["title"] or "")
                )
                self.list.addItem(item)

        self.summary.setText(
            f"{len(self.groups):,} dubbele groepen gevonden | "
            f"{duplicate_files:,} overtollige kopieen | "
            f"{len(self.ignored_keys):,} genegeerd"
        )
        self.refresh_button_state()

    def refresh_button_state(self):
        group_count = 0
        file_count = 0

        for item in self.list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(data, dict):
                continue

            if data.get("kind") == "group":
                group_count += 1
            elif data.get("kind") == "file" and not data.get("linked"):
                file_count += 1

        self.ignore_button.setEnabled(group_count > 0)
        self.unignore_button.setEnabled(group_count > 0)
        self.delete_button.setEnabled(file_count > 0)

        self.ignore_button.setText(
            f"[ GESELECTEERDE GROEPEN NEGEREN ({group_count}) ]"
        )
        self.unignore_button.setText(
            f"[ NEGEREN OPHEFFEN ({group_count}) ]"
        )
        self.delete_button.setText(
            f"[ GESELECTEERDE BESTANDEN VERWIJDEREN ({file_count}) ]"
        )

    def selected_group_keys(self):
        return {
            data.get("group_key")
            for item in self.list.selectedItems()
            for data in [item.data(Qt.ItemDataRole.UserRole)]
            if isinstance(data, dict) and data.get("kind") == "group" and data.get("group_key")
        }

    def ignore_selected_groups(self):
        keys = self.selected_group_keys()
        if not keys:
            return

        self.ignored_keys.update(keys)
        save_ignored_keys(self.ignored_keys)
        self.scan()

    def unignore_selected_groups(self):
        keys = self.selected_group_keys()
        if not keys:
            return

        self.ignored_keys.difference_update(keys)
        save_ignored_keys(self.ignored_keys)
        self.show_ignored.setChecked(True)
        self.scan()

    def selected_files(self):
        result = []
        for item in self.list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole)
            if (
                isinstance(data, dict)
                and data.get("kind") == "file"
                and not data.get("linked")
            ):
                result.append(data)
        return result

    def delete_selected_files(self):
        selected = self.selected_files()
        if not selected:
            return

        preview = "\n".join(
            str(data["path"])
            for data in selected[:10]
        )
        if len(selected) > 10:
            preview += "\n..."

        answer = QMessageBox.question(
            self,
            "DEFINITIEF VERWIJDEREN",
            (
                f"Je gaat {len(selected)} MP3-bestand(en) ECHT van de harde schijf verwijderen.\n\n"
                f"{preview}\n\n"
                "Doorgaan?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        errors = []

        conn = get_connection()
        try:
            for data in selected:
                try:
                    Path(str(data["path"])).unlink()
                    conn.execute(
                        "DELETE FROM mp3_files WHERE id=?",
                        (int(data["id"]),),
                    )
                    deleted += 1
                except Exception as exc:
                    errors.append(f"{data['path']}\n{exc}")

            conn.commit()
        finally:
            conn.close()

        message = f"{deleted} MP3-bestand(en) definitief van de schijf verwijderd."
        if errors:
            message += "\n\nNiet verwijderd:\n" + "\n\n".join(errors[:5])

        QMessageBox.information(self, "Resultaat", message)
        self.scan()

    def closeEvent(self, event):
        self._closing = True
        worker = self.worker
        if worker is not None and worker.isRunning():
            worker.request_stop()
            worker.wait()
        self.worker = None
        event.accept()
