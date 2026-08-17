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
)

from database.database import get_connection


_COPY_SUFFIX_RE = re.compile(r"\s*(?:\([0-9]+\)|\[[0-9]+\]|[_-](?:copy|kopie|[0-9]+))\s*$", re.I)


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

                mp3_id, path, artist, title, album, year, checked, linked = row
                path = str(path or "")
                if not path:
                    processed += 1
                    self.progress.emit(processed, total)
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

                # Same normalized artist/title. Version names such as
                # Remix, Club Mix, Rap Version, Instrumental, etc. are
                # deliberately NOT stripped, so different versions remain
                # separate tracks.
                groups.append(
                    {
                        "kind": "track",
                        "key": key,
                        "files": members,
                    }
                )

            # Sort biggest groups first, then artist/title.
            groups.sort(
                key=lambda group: (
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
        self.resize(1100, 760)
        self.groups = []
        self.worker = None
        self._closing = False

        root = QVBoxLayout(self)
        root.setSpacing(10)

        title = QLabel("MP3 DUBBELE TRACKS")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)

        info = QLabel(
            "Deze scan zoekt dezelfde artiest + titel. Duidelijke versies zoals "
            "Remix, Club Mix, Rap Version, Instrumental, Live, enz. blijven "
            "afzonderlijk zichtbaar. Een kopie zoals '(1)' wordt wel als dezelfde "
            "track herkend. Er wordt niets automatisch verwijderd."
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
        root.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("[ SCAN DUBBELS ]")
        self.delete_button = QPushButton("[ GESELECTEERDE DUBBELE VERWIJDEREN ]")
        self.delete_button.setEnabled(False)
        self.close_button = QPushButton("[ SLUITEN ]")

        actions.addWidget(self.scan_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
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

        self.worker = HashWorker(self)
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

    def on_failed(self, message):
        self.scan_button.setEnabled(True)
        if not self._closing:
            QMessageBox.critical(
                self,
                "Dubbel-scan mislukt",
                message,
            )

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
        self.delete_button.setEnabled(False)

        if not self.groups:
            self.summary.setText(
                "Geen dubbele tracks gevonden."
            )
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

            header = QListWidgetItem(
                f"DUBBEL GROEP {group_index}  •  "
                f"{artist} — {title}  •  {len(members)} BESTANDEN"
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

                label = (
                    f"    {'★' if member_index == 0 else '•'}  "
                    f"{Path(member['path']).name}"
                )

                if member["album"]:
                    label += f"  |  {member['album']}"
                if member["year"]:
                    label += f"  |  {member['year']}"
                if flags:
                    label += "  [" + " • ".join(flags) + "]"

                item = QListWidgetItem(label)
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

        self.summary.setText(
            f"{len(self.groups):,} dubbele trackgroepen gevonden  •  "
            f"{duplicate_files:,} overtollige kopieën"
        )

    def on_selection_changed(self):
        selected = self.list.currentItem()
        data = (
            selected.data(Qt.ItemDataRole.UserRole)
            if selected
            else None
        )
        self.delete_button.setEnabled(
            bool(
                data
                and data.get("kind") == "file"
                and not data.get("linked")
            )
        )

    def delete_selected(self):
        selected = self.list.currentItem()
        data = (
            selected.data(Qt.ItemDataRole.UserRole)
            if selected
            else None
        )

        if not data or data.get("kind") != "file":
            return

        if data.get("linked"):
            QMessageBox.warning(
                self,
                "Beschermd bestand",
                "Dit MP3-bestand is aan een VinylVault-track gekoppeld "
                "en wordt niet verwijderd."
            )
            return

        path = str(data.get("path") or "")
        mp3_id = int(data.get("id"))

        answer = QMessageBox.question(
            self,
            "Dubbele MP3 verwijderen",
            f"Verwijder deze dubbele MP3?\n\n{path}",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
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
