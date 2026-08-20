from pathlib import Path

TARGET = Path("gui/mp3_duplicate_cleaner.py")

CODE = r'''from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
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


def norm_text(value):
    value = str(value or "").strip().casefold()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def norm_title(value):
    value = norm_text(value)
    while True:
        cleaned = _COPY_SUFFIX_RE.sub("", value).strip(" -_")
        if cleaned == value:
            return value
        value = cleaned


def track_key(artist, title):
    artist_n = norm_text(artist)
    title_n = norm_title(title)
    if not artist_n or not title_n:
        return ""
    return f"{artist_n}|||{title_n}"


def duration_text(path, db_duration):
    try:
        seconds = float(db_duration)
        if seconds > 0:
            seconds = int(round(seconds))
            return f"{seconds // 60}:{seconds % 60:02d}"
    except Exception:
        pass

    if MUTAGEN_AVAILABLE and Path(path).is_file():
        try:
            seconds = int(round(float(MP3(path).info.length)))
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


class DuplicateWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stop_requested = False

    def request_stop(self):
        self.stop_requested = True
        self.requestInterruption()

    def run(self):
        try:
            conn = get_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT m.id, m.path, m.artist, m.title, m.album, m.year,
                           m.duration, COALESCE(m.metadata_checked, 0),
                           EXISTS(SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id)
                    FROM mp3_files m
                    WHERE m.path IS NOT NULL
                    ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE,
                             m.path COLLATE NOCASE
                    """
                ).fetchall()
            finally:
                conn.close()

            total = len(rows)
            processed = 0
            groups = defaultdict(list)

            for row in rows:
                if self.stop_requested or self.isInterruptionRequested():
                    return

                mp3_id, path, artist, title, album, year, db_duration, checked, linked = row
                path = str(path or "")
                if path and Path(path).is_file():
                    key = track_key(artist, title)
                    if key:
                        groups[key].append({
                            "id": int(mp3_id),
                            "path": path,
                            "artist": str(artist or "").strip(),
                            "title": str(title or "").strip(),
                            "album": str(album or "").strip(),
                            "year": year,
                            "duration": db_duration,
                            "checked": int(checked or 0),
                            "linked": int(linked or 0),
                        })

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

            result = []
            for key, members in groups.items():
                if self.stop_requested or self.isInterruptionRequested():
                    return
                if len(members) >= 2:
                    result.append({
                        "track_key": key,
                        "ignored": key in ignored,
                        "members": members,
                    })

            result.sort(key=lambda g: (
                g["ignored"],
                -len(g["members"]),
                g["members"][0]["artist"].casefold(),
                g["members"][0]["title"].casefold(),
            ))

            self.finished_scan.emit(result)

        except Exception as exc:
            self.failed.emit(str(exc))


class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MP3 DUBBELE TRACKS")
        self.resize(1200, 850)
        self.worker = None
        self.groups = []
        self._closing = False
        self._group_checks = []
        self._file_checks = []
        self.show_ignored = False

        ensure_ignore_table()

        root = QVBoxLayout(self)
        root.setSpacing(10)

        title = QLabel("MP3 DUBBELE TRACKS")
        title.setStyleSheet("font-size:24px;font-weight:900;color:#fff;")
        root.addWidget(title)

        info = QLabel(
            "Elke groep toont de volledige paden en speelduur. "
            "Vink bestanden aan voor definitieve verwijdering. "
            "Vink een groepsvak aan om de groep als GEEN ECHTE DUBBEL te negeren."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#aaaab3;")
        root.addWidget(info)

        self.progress = QProgressBar()
        root.addWidget(self.progress)

        self.summary = QLabel("Nog niet gescand.")
        self.summary.setStyleSheet("color:#d84b91;font-weight:bold;")
        root.addWidget(self.summary)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(12)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("[ SCAN DUBBELS ]")
        self.delete_button = QPushButton("[ AANGEVINKTE BESTANDEN VERWIJDEREN ]")
        self.ignore_button = QPushButton("[ AANGEVINKTE GROEPEN NEGEREN ]")
        self.toggle_ignored_button = QPushButton("[ TOON GENEGEERDE ]")
        self.close_button = QPushButton("[ SLUITEN ]")
        self.delete_button.setEnabled(False)
        self.ignore_button.setEnabled(False)

        actions.addWidget(self.scan_button)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.ignore_button)
        actions.addWidget(self.toggle_ignored_button)
        actions.addStretch()
        actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
        self.delete_button.clicked.connect(self.delete_checked)
        self.ignore_button.clicked.connect(self.ignore_checked_groups)
        self.toggle_ignored_button.clicked.connect(self.toggle_ignored)
        self.close_button.clicked.connect(self.reject)

        self.setStyleSheet(
            """
            QDialog { background:#0b0b0f; color:#f2f2f5; }
            QScrollArea { background:#0f0f14; border:1px solid #25252d; }
            QWidget#groupBox { background:#14141b; border:1px solid #30303a; border-radius:8px; }
            QLabel { color:#f2f2f5; }
            QCheckBox { color:#fff; spacing:8px; padding:4px; }
            QCheckBox::indicator { width:20px; height:20px; border:2px solid #8a8a96; border-radius:4px; background:#101015; }
            QCheckBox::indicator:checked { background:#d84b91; border-color:#d84b91; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a; border-radius:6px; padding:8px 10px; }
            QPushButton:hover { border-color:#d84b91; background:#24242c; }
            QProgressBar { border:1px solid #30303a; background:#18181f; height:12px; border-radius:5px; }
            QProgressBar::chunk { background:#d84b91; border-radius:5px; }
            """
        )

        self.scan()

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._group_checks.clear()
        self._file_checks.clear()

    def scan(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self._closing = False
        self.clear_content()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.summary.setText("Scannen van MP3's...")
        self.scan_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.ignore_button.setEnabled(False)

        self.worker = DuplicateWorker(self)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_progress(self, processed, total):
        self.progress.setValue(int(processed * 100 / total) if total else 0)
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
        self.clear_content()
        visible = [g for g in self.groups if self.show_ignored or not g["ignored"]]
        ignored_count = sum(1 for g in self.groups if g["ignored"])

        if not visible:
            self.summary.setText(f"Geen zichtbare dubbele groepen. {ignored_count} genegeerd.")
            self.scan_button.setEnabled(True)
            return

        duplicate_files = sum(len(g["members"]) - 1 for g in visible)

        for index, group in enumerate(visible, 1):
            box = QWidget()
            box.setObjectName("groupBox")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 10, 10, 10)
            box_layout.setSpacing(6)

            group_cb = QCheckBox(
                f"GROEP {index}: {group['members'][0]['artist']} - "
                f"{group['members'][0]['title']} ({len(group['members'])} bestanden)"
            )
            group_cb.setToolTip(group["track_key"])
            group_cb.setProperty("track_key", group["track_key"])
            group_cb.setProperty("ignored", group["ignored"])
            if group["ignored"]:
                group_cb.setText(group_cb.text() + " [GENEGEERD]")
            group_cb.stateChanged.connect(self.update_buttons)
            box_layout.addWidget(group_cb)
            self._group_checks.append(group_cb)

            for member in group["members"]:
                duration = duration_text(member["path"], member["duration"])
                row = QCheckBox(
                    f"{Path(member['path']).name} | DUUR {duration}\n"
                    f"PAD: {member['path']}"
                )
                row.setToolTip(member["path"])
                row.setProperty("path", member["path"])
                row.setProperty("mp3_id", member["id"])
                row.setProperty("linked", bool(member["linked"]))
                row.setProperty("track_key", group["track_key"])
                row.setStyleSheet(
                    "QCheckBox { margin-left:28px; color:#e5e5ea; }"
                )
                row.stateChanged.connect(self.update_buttons)
                if member["linked"]:
                    row.setEnabled(False)
                    row.setText(row.text() + " [VINYL GEKOPPELD]")
                box_layout.addWidget(row)
                self._file_checks.append(row)

            self.content_layout.addWidget(box)

        self.content_layout.addStretch(1)
        self.summary.setText(
            f"{len(visible):,} groepen zichtbaar | "
            f"{duplicate_files:,} overtollige kandidaten | "
            f"{ignored_count:,} genegeerd"
        )
        self.scan_button.setEnabled(True)
        self.update_buttons()

    def update_buttons(self, *_args):
        delete_count = sum(1 for cb in self._file_checks if cb.isChecked() and cb.isEnabled())
        ignore_count = sum(1 for cb in self._group_checks if cb.isChecked() and not cb.property("ignored"))
        unignore_count = sum(1 for cb in self._group_checks if cb.isChecked() and cb.property("ignored"))
        self.delete_button.setEnabled(delete_count > 0)
        self.ignore_button.setEnabled(ignore_count > 0 or unignore_count > 0)
        self.delete_button.setText(f"[ AANGEVINKTE BESTANDEN VERWIJDEREN ({delete_count}) ]")
        self.ignore_button.setText(
            f"[ {'NEGEREN' if ignore_count else 'NEGEREN OPHEFFEN'} ({ignore_count or unignore_count}) ]"
        )

    def ignore_checked_groups(self):
        checked = [cb for cb in self._group_checks if cb.isChecked()]
        if not checked:
            return

        conn = get_connection()
        try:
            for cb in checked:
                key = str(cb.property("track_key") or "")
                if not key:
                    continue
                if cb.property("ignored"):
                    conn.execute("DELETE FROM mp3_duplicate_ignored WHERE track_key=?", (key,))
                else:
                    conn.execute("INSERT OR IGNORE INTO mp3_duplicate_ignored(track_key) VALUES(?)", (key,))
            conn.commit()
        finally:
            conn.close()
        self.scan()

    def delete_checked(self):
        checked = [cb for cb in self._file_checks if cb.isChecked() and cb.isEnabled()]
        if not checked:
            return

        paths = [str(cb.property("path") or "") for cb in checked]
        answer = QMessageBox.question(
            self,
            "ECHT VERWIJDEREN",
            f"Dit verwijdert {len(paths)} bestand(en) ECHT van de harde schijf.\n\n"
            + "\n".join(paths[:10])
            + ("\n..." if len(paths) > 10 else "")
            + "\n\nDoorgaan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        errors = []
        conn = get_connection()
        try:
            for cb in checked:
                path = str(cb.property("path") or "")
                mp3_id = int(cb.property("mp3_id"))
                try:
                    Path(path).unlink()
                    conn.execute("DELETE FROM mp3_files WHERE id=?", (mp3_id,))
                except Exception as exc:
                    errors.append(f"{path}: {exc}")
            conn.commit()
        finally:
            conn.close()

        if errors:
            QMessageBox.warning(self, "Enkele bestanden niet verwijderd", "\n".join(errors[:10]))
        self.scan()

    def toggle_ignored(self):
        self.show_ignored = not self.show_ignored
        self.toggle_ignored_button.setText(
            "[ TOON NORMALE ]" if self.show_ignored else "[ TOON GENEGEERDE ]"
        )
        if self.groups:
            self.on_finished(self.groups)
        else:
            self.scan()

    def closeEvent(self, event):
        self._closing = True
        if self.worker is not None and self.worker.isRunning():
            self.worker.request_stop()
            self.worker.wait()
        self.worker = None
        event.accept()
'''

TARGET.write_text(CODE, encoding="utf-8-sig")
print(f"OK: {TARGET} vervangen door echte widget-checkbox versie.")
'''

Path("tools/apply/replace_mp3_duplicate_cleaner_real_checkboxes.py").write_text(CODE, encoding="utf-8-sig")
print("Installer aangemaakt")
