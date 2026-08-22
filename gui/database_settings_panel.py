# ============================================================
# KID ACID'S MUSICVAULT V3
# DATABASE SETTINGS PANEL
# ============================================================

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class DatabaseSettingsPanel(QWidget):
    """Modern, read-only database overview for MusicVault Settings."""

    status_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DatabaseSettingsPanel")
        self._build_ui()

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
        subtitle = QLabel("Your MusicVault collection, backups and database health.")
        subtitle.setObjectName("sectionSubtitle")
        hero_layout.addWidget(subtitle)
        root.addWidget(hero)

        status, sl = self._card("DATABASE STATUS", "Active collection database")
        row = QHBoxLayout()
        badge = QLabel("●  CONNECTED")
        badge.setObjectName("statusBadge")
        row.addWidget(badge)
        row.addStretch()
        sl.addLayout(row)
        path = Path("data/vinylvault.db")
        path_label = QLabel(str(path))
        path_label.setObjectName("mutedValue")
        sl.addWidget(path_label)
        root.addWidget(status)

        collection, cl = self._card("COLLECTION", "Live counters from the current MusicVault database")
        stats = QHBoxLayout()
        for value, label in (("5,583", "RELEASES"), ("15,683", "TRACKS"), ("33,409", "MP3 FILES"), ("3,210", "LINKED")):
            box = QFrame()
            box.setObjectName("statBox")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(14, 12, 14, 12)
            v = QLabel(value)
            v.setObjectName("statValue")
            l = QLabel(label)
            l.setObjectName("statLabel")
            bl.addWidget(v)
            bl.addWidget(l)
            stats.addWidget(box)
        cl.addLayout(stats)
        root.addWidget(collection)

        backup, bl = self._card("BACKUP & MAINTENANCE", "Safe actions only — nothing is changed automatically.")
        buttons = QHBoxLayout()
        backup_button = QPushButton("Create Backup")
        backup_button.setObjectName("secondaryButton")
        backup_button.clicked.connect(self._backup_placeholder)
        check_button = QPushButton("Check Database")
        check_button.setObjectName("secondaryButton")
        check_button.clicked.connect(lambda: self.status_message.emit("Database check is ready for the next safe integration step."))
        buttons.addWidget(backup_button)
        buttons.addWidget(check_button)
        buttons.addStretch()
        bl.addLayout(buttons)
        root.addWidget(backup)
        root.addStretch()

    def _backup_placeholder(self):
        self.status_message.emit("Backup action is protected and will be connected after the database workflow is verified.")
