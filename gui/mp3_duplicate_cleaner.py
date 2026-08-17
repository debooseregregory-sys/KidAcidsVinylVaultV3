from __future__ import annotations

import hashlib
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


class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

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
                            SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id = m.id
                        )
                    FROM mp3_files m
                    ORDER BY m.path COLLATE NOCASE
                    """
                ).fetchall()
            finally:
                conn.close()

            files = []
            total = len(rows)
            processed = 0
            by_size = {}

            for row in rows:
                mp3_id, path, artist, title, album, year, checked, linked = row
                path_obj = Path(str(path or ""))
                if not path_obj.is_file():
                    processed += 1
                    self.progress.emit(processed, total)
                    continue

                try:
                    size = path_obj.stat().st_size
                except OSError:
                    processed += 1
                    self.progress.emit(processed, total)
                    continue

                by_size.setdefault(size, []).append(
                    (mp3_id, str(path_obj), artist, title, album, year, checked, linked)
                )
                processed += 1
                self.progress.emit(processed, total)

            groups = []
            for size, candidates in by_size.items():
                if len(candidates) < 2:
                    continue

                hashed = {}
                for item in candidates:
                    path = item[1]
                    h = hashlib.sha256()
                    try:
                        with open(path, "rb") as fh:
                            while True:
                                chunk = fh.read(1024 * 1024)
                                if not chunk:
                                    break
                                h.update(chunk)
                    except OSError:
                        continue
                    hashed.setdefault(h.hexdigest(), []).append(item)

                for sha256, members in hashed.items():
                    if len(members) > 1:
                        groups.append(
                            {
                                "sha256": sha256,
                                "size": size,
                                "files": members,
                            }
                        )

            self.finished_scan.emit(groups)
        except Exception as exc:
            self.failed.emit(str(exc))


class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MP3 DUBBELE BESTANDEN")
        self.resize(980, 720)
        self.groups = []
        self.worker = None

        root = QVBoxLayout(self)
        root.setSpacing(10)

        title = QLabel("MP3 DUBBELE BESTANDEN")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)

        info = QLabel(
            "Identieke MP3-inhoud wordt op SHA-256 gevonden. "
            "Verwijderen gebeurt pas nadat jij een bestand hebt geselecteerd."
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
        if self.worker and self.worker.isRunning():
            return
        self.list.clear()
        self.summary.setText("Scannen van MP3's...")
        self.progress.setValue(0)
        self.scan_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.worker = HashWorker(self)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_progress(self, processed, total):
        value = int((processed / total) * 100) if total else 0
        self.progress.setValue(value)
        self.summary.setText(f"Scannen: {processed} / {total} MP3's")

    def on_failed(self, message):
        self.scan_button.setEnabled(True)
        QMessageBox.critical(self, "Dubbel-scan mislukt", message)

    def on_finished(self, groups):
        self.groups = groups
        self.scan_button.setEnabled(True)
        self.progress.setValue(100)
        self.list.clear()

        duplicate_files = 0
        for group_index, group in enumerate(groups, 1):
            members = group["files"]
            duplicate_files += len(members) - 1

            # First item is only a preview; no automatic delete decision is made.
            header = QListWidgetItem(
                f"DUBBEL GROEP {group_index}  •  {len(members)} IDENTIEKE BESTANDEN  •  {group['size']:,} bytes"
            )
            header.setData(Qt.ItemDataRole.UserRole, {"kind": "header", "group": group_index - 1})
            self.list.addItem(header)

            for member_index, item in enumerate(members):
                mp3_id, path, artist, title, album, year, checked, linked = item
                flags = []
                if linked:
                    flags.append("VINYL GEKOPPELD")
                if checked:
                    flags.append("METADATA KLAAR")
                flag_text = "  •  ".join(flags) if flags else ""
                label = f"    {'★' if member_index == 0 else '•'}  {Path(path).name}"
                if artist or title:
                    label += f"  —  {artist or ''} — {title or ''}".rstrip(" —")
                if flag_text:
                    label += f"  [{flag_text}]"

                widget_item = QListWidgetItem(label)
                widget_item.setToolTip(path)
                widget_item.setData(
                    Qt.ItemDataRole.UserRole,
                    {
                        "kind": "file",
                        "group": group_index - 1,
                        "member": member_index,
                        "path": path,
                        "id": mp3_id,
                        "linked": linked,
                    },
                )
                self.list.addItem(widget_item)

        self.summary.setText(
            f"{len(groups)} dubbele groepen gevonden • {duplicate_files} overtollige bestanden"
        )

    def on_selection_changed(self):
        selected = self.list.currentItem()
        data = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        self.delete_button.setEnabled(
            bool(data and data.get("kind") == "file" and not data.get("linked"))
        )

    def delete_selected(self):
        selected = self.list.currentItem()
        data = selected.data(Qt.ItemDataRole.UserRole) if selected else None
        if not data or data.get("kind") != "file":
            return

        path = str(data.get("path") or "")
        mp3_id = int(data.get("id"))
        if data.get("linked"):
            QMessageBox.warning(
                self,
                "Beschermd bestand",
                "Dit MP3-bestand is aan een VinylVault-track gekoppeld en wordt niet verwijderd."
            )
            return

        answer = QMessageBox.question(
            self,
            "Dubbel bestand verwijderen",
            f"Verwijder dit dubbele MP3-bestand?\n\n{path}",
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
