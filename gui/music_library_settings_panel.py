# ============================================================
# KID ACID'S MUSICVAULT V3
# MUSIC LIBRARY SETTINGS PANEL
# ============================================================

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class MusicLibrarySettingsPanel(QWidget):
    """Modern, read-only Music Library settings panel.

    This first version deliberately exposes library information without
    changing the database or MP3 links. Actions can be wired safely later.
    """

    action_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _card(self):
        card = QFrame()
        card.setObjectName("musicLibraryCard")
        card.setStyleSheet("""
            QFrame#musicLibraryCard {
                background: #17171d;
                border: 1px solid #2d2d36;
                border-radius: 18px;
            }
            QLabel { color: #f4f4f7; }
            QLabel.muted { color: #92929d; }
            QPushButton {
                background: #24242d;
                color: #f5f5f7;
                border: 1px solid #3a3a45;
                border-radius: 10px;
                padding: 9px 16px;
                font-weight: 700;
            }
            QPushButton:hover { border-color: #d84b91; background: #2b2029; }
        """)
        return card

    def _stat(self, value, label):
        box = QFrame()
        box.setStyleSheet("QFrame { background:#111116; border-radius:14px; }")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(18, 16, 18, 16)
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size:24px;font-weight:900;color:#ffffff;")
        caption = QLabel(label.upper())
        caption.setStyleSheet("font-size:10px;font-weight:800;letter-spacing:1px;color:#8d8d98;")
        lay.addWidget(value_label)
        lay.addWidget(caption)
        return box

    def _section_title(self, title, subtitle):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:21px;font-weight:900;color:#ffffff;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setProperty("class", "muted")
        subtitle_label.setStyleSheet("font-size:12px;color:#90909b;")
        return title_label, subtitle_label

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(18)

        eyebrow = QLabel("MUSIC LIBRARY")
        eyebrow.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:2px;color:#d84b91;")
        root.addWidget(eyebrow)

        title, subtitle = self._section_title(
            "Your collection, at a glance",
            "Manage your music sources and matching workflow from one place."
        )
        root.addWidget(title)
        root.addWidget(subtitle)

        overview = self._card()
        ol = QVBoxLayout(overview)
        ol.setContentsMargins(20, 20, 20, 20)
        ol.setSpacing(14)

        health_row = QHBoxLayout()
        health = QLabel("●  LIBRARY READY")
        health.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:1px;color:#72d69a;")
        health_row.addWidget(health)
        health_row.addStretch()
        source = QLabel("MP3 SOURCE")
        source.setStyleSheet("font-size:10px;font-weight:800;letter-spacing:1px;color:#777782;")
        health_row.addWidget(source)
        ol.addLayout(health_row)

        stats = QHBoxLayout()
        stats.setSpacing(10)
        stats.addWidget(self._stat("33,409", "MP3 FILES"))
        stats.addWidget(self._stat("15,683", "TRACKS"))
        stats.addWidget(self._stat("3,210", "LINKED TRACKS"))
        stats.addWidget(self._stat("—", "MISSING LINKS"))
        ol.addLayout(stats)
        root.addWidget(overview)

        folders = self._card()
        fl = QVBoxLayout(folders)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(12)
        ft, fs = self._section_title("Music folder", "The source location used by your MusicVault library.")
        fl.addWidget(ft)
        fl.addWidget(fs)
        path_row = QHBoxLayout()
        path_label = QLabel(r"D:\01. MP3’s")
        path_label.setStyleSheet("background:#111116;border-radius:10px;padding:12px;color:#d5d5dc;font-family:Consolas;font-size:12px;")
        path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        path_row.addWidget(path_label)
        open_btn = QPushButton("Open Folder")
        open_btn.clicked.connect(lambda: self.action_requested.emit("open_folder"))
        path_row.addWidget(open_btn)
        fl.addLayout(path_row)
        root.addWidget(folders)

        workflow = self._card()
        wl = QVBoxLayout(workflow)
        wl.setContentsMargins(20, 20, 20, 20)
        wl.setSpacing(12)
        wt, ws = self._section_title("Library workflow", "Safe shortcuts for the tools already in MusicVault.")
        wl.addWidget(wt)
        wl.addWidget(ws)
        buttons = QHBoxLayout()
        for text, action in (("Scan Library", "scan"), ("Find Missing", "missing"), ("Review Matches", "matches")):
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, a=action: self.action_requested.emit(a))
            buttons.addWidget(button)
        wl.addLayout(buttons)
        root.addWidget(workflow)
        root.addStretch()
