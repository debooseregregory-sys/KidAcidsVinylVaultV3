# ============================================================
# KID ACID'S MUSICVAULT V3
# DATABASE SETTINGS PANEL
# ============================================================

from datetime import datetime
from pathlib import Path
import sqlite3

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from database.database import DB_PATH, get_connection


class DatabaseSettingsPanel(QWidget):
    """Live database overview with safe integrity check and SQLite backup."""

    status_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DatabaseSettingsPanel")
        self._stat_labels = {}
        self._status_badge = None
        self._health_label = None
        self._build_ui()
        self.refresh()

    def _card(self, title, subtitle=""):
        card = QFrame()
        card.setObjectName("settingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("cardTitle")
        layout.addWidget(heading)
        if subtitle:
            text = QLabel(subtitle)
            text.setObjectName("cardSubtitle")
            text.setWordWrap(True)
            layout.addWidget(text)
        return card, layout

    def _stat(self, value, label, key):
        box = QFrame()
        box.setObjectName("statBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 12, 14, 12)
        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        label_widget = QLabel(label)
        label_widget.setObjectName("statLabel")
        layout.addWidget(value_label)
        layout.addWidget(label_widget)
        self._stat_labels[key] = value_label
        return box

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("databaseHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        title = QLabel("DATABASE")
        title.setObjectName("sectionTitle")
        hero_layout.addWidget(title)
        subtitle = QLabel("Your MusicVault collection, database health and safe backup tools.")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)
        root.addWidget(hero)

        status, sl = self._card("DATABASE STATUS", "Live information from the active MusicVault database.")
        row = QHBoxLayout()
        self._status_badge = QLabel("●  CHECKING")
        self._status_badge.setObjectName("statusBadge")
        row.addWidget(self._status_badge)
        row.addStretch()
        self._health_label = QLabel("")
        self._health_label.setObjectName("cardSubtitle")
        row.addWidget(self._health_label)
        sl.addLayout(row)
        path_label = QLabel(str(DB_PATH))
        path_label.setObjectName("mutedValue")
        path_label.setWordWrap(True)
        sl.addWidget(path_label)
        self._size_label = QLabel("")
        self._size_label.setObjectName("cardSubtitle")
        sl.addWidget(self._size_label)
        root.addWidget(status)

        collection, cl = self._card("COLLECTION", "Current record counts — read-only.")
        stats = QHBoxLayout()
        stats.setSpacing(10)
        stats.addWidget(self._stat("—", "RELEASES", "releases"))
        stats.addWidget(self._stat("—", "TRACKS", "tracks"))
        stats.addWidget(self._stat("—", "MP3 FILES", "mp3"))
        stats.addWidget(self._stat("—", "LINKED", "linked"))
        cl.addLayout(stats)
        root.addWidget(collection)

        backup, bl = self._card("BACKUP & MAINTENANCE", "Safe actions only. Backup uses SQLite's online backup API and does not alter the live database.")
        buttons = QHBoxLayout()
        backup_button = QPushButton("Create Backup")
        backup_button.setObjectName("secondaryButton")
        backup_button.clicked.connect(self._create_backup)
        buttons.addWidget(backup_button)
        check_button = QPushButton("Check Database")
        check_button.setObjectName("secondaryButton")
        check_button.clicked.connect(self._check_database)
        buttons.addWidget(check_button)
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self.refresh)
        buttons.addWidget(refresh_button)
        buttons.addStretch()
        bl.addLayout(buttons)
        root.addWidget(backup)
        root.addStretch()

        self.setStyleSheet("""
            QFrame#databaseHero, QFrame#settingsCard { background:#17171d; border:1px solid #2d2d36; border-radius:18px; }
            QLabel#sectionTitle { color:#fff; font-size:21px; font-weight:900; letter-spacing:1px; }
            QLabel#sectionSubtitle, QLabel#cardSubtitle { color:#90909b; font-size:12px; }
            QLabel#cardTitle { color:#fff; font-size:15px; font-weight:900; }
            QLabel#mutedValue { background:#111116; border-radius:10px; padding:11px; color:#d5d5dc; font-family:Consolas; font-size:11px; }
            QFrame#statBox { background:#111116; border-radius:14px; }
            QLabel#statValue { color:#fff; font-size:23px; font-weight:900; }
            QLabel#statLabel { color:#8d8d98; font-size:9px; font-weight:900; letter-spacing:1px; }
            QLabel#statusBadge { background:#17251e; border:1px solid #315f47; border-radius:12px; padding:6px 10px; color:#72d69a; font-size:9px; font-weight:900; letter-spacing:1px; }
            QPushButton#secondaryButton { background:#24242d; color:#f5f5f7; border:1px solid #3a3a45; border-radius:10px; padding:9px 16px; font-weight:700; }
            QPushButton#secondaryButton:hover { border-color:#d84b91; background:#2b2029; }
        """)

    def refresh(self):
        try:
            connection = get_connection()
            try:
                counts = {
                    "releases": connection.execute("SELECT COUNT(*) FROM releases").fetchone()[0],
                    "tracks": connection.execute("SELECT COUNT(*) FROM tracks").fetchone()[0],
                    "mp3": connection.execute("SELECT COUNT(*) FROM mp3_files").fetchone()[0],
                    "linked": connection.execute("SELECT COUNT(DISTINCT track_id) FROM track_mp3").fetchone()[0],
                }
            finally:
                connection.close()
            for key, value in counts.items():
                self._stat_labels[key].setText(f"{value:,}")
            if DB_PATH.exists():
                self._size_label.setText(f"Database size: {DB_PATH.stat().st_size / (1024 * 1024):.2f} MB")
            else:
                self._size_label.setText("Database file not found")
            self._status_badge.setText("●  CONNECTED")
            self._health_label.setText("Ready")
        except sqlite3.Error as exc:
            for label in self._stat_labels.values():
                label.setText("—")
            self._status_badge.setText("●  DATABASE ERROR")
            self._health_label.setText(str(exc))

    def _check_database(self):
        try:
            connection = sqlite3.connect(DB_PATH, timeout=30.0)
            try:
                result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                connection.close()
            if result == "ok":
                self._status_badge.setText("●  HEALTHY")
                self._health_label.setText("SQLite integrity check passed")
                QMessageBox.information(self, "Database Check", "Database integrity check geslaagd.\n\nDe database is niet gewijzigd.")
            else:
                self._status_badge.setText("●  CHECK FAILED")
                self._health_label.setText("Integrity check reported an issue")
                QMessageBox.warning(self, "Database Check", f"SQLite integrity check gaf een probleem terug:\n\n{result}")
        except (sqlite3.Error, OSError) as exc:
            QMessageBox.critical(self, "Database Check", f"Controle mislukt:\n\n{exc}")

    def _create_backup(self):
        if not DB_PATH.exists():
            QMessageBox.warning(self, "Create Backup", "De actieve database bestaat niet.")
            return
        backup_dir = DB_PATH.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"vinylvault_backup_{timestamp}.db"
        source = None
        target = None
        try:
            source = sqlite3.connect(DB_PATH, timeout=30.0)
            target = sqlite3.connect(backup_path)
            with target:
                source.backup(target)
            target.close()
            target = None
            self.status_message.emit(f"Backup created: {backup_path.name}")
            QMessageBox.information(self, "Backup Created", f"Veilige backup gemaakt.\n\n{backup_path}")
        except (sqlite3.Error, OSError) as exc:
            try:
                if backup_path.exists():
                    backup_path.unlink()
            except OSError:
                pass
            QMessageBox.critical(self, "Create Backup", f"Backup mislukt:\n\n{exc}")
        finally:
            if target is not None:
                target.close()
            if source is not None:
                source.close()
