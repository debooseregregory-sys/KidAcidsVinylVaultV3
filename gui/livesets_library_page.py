from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"


class LivesetsLibraryPage(QWidget):
    showcase_requested = Signal()
    edit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.reload()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("LIVESETS")
        title.setObjectName("livesetsHeader")
        root.addWidget(title)
        line = QFrame()
        line.setObjectName("livesetsLine")
        line.setFixedHeight(2)
        line.setMaximumWidth(150)
        root.addWidget(line)

        subtitle = QLabel("Beheer je livesets en kies welke showcase je wilt bekijken.")
        subtitle.setObjectName("livesetsSub")
        root.addWidget(subtitle)

        actions = QHBoxLayout()
        self.showcase_button = QPushButton("▶  LIVESETS SHOWCASE")
        self.showcase_button.clicked.connect(self.showcase_requested.emit)
        self.edit_button = QPushButton("✎  LIVESETS BEWERKEN")
        self.edit_button.clicked.connect(self.edit_requested.emit)
        actions.addWidget(self.showcase_button)
        actions.addWidget(self.edit_button)
        actions.addStretch(1)
        root.addLayout(actions)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{border:0;background:transparent;}")
        self.content = QWidget()
        self.list_layout = QVBoxLayout(self.content)
        self.list_layout.setContentsMargins(0, 4, 0, 20)
        self.list_layout.setSpacing(8)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet("""
            QLabel#livesetsHeader{color:#fff;font-size:28px;font-weight:900;}
            QLabel#livesetsSub{color:#858591;font-size:13px;}
            QFrame#livesetsLine{background:#ffcf72;border-radius:1px;}
            QPushButton{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:7px;padding:10px 16px;font-size:12px;font-weight:800;}
            QPushButton:hover{background:#24242c;border-color:#ffcf72;}
            QFrame#liveRow{background:#121217;border:1px solid #292933;border-radius:8px;}
            QLabel#liveTitle{color:#fff;font-size:14px;font-weight:900;}
            QLabel#liveMeta{color:#858591;font-size:12px;}
        """)

    def reload(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError, json.JSONDecodeError):
            items = []
        if not items:
            label = QLabel("Nog geen livesets toegevoegd.")
            label.setObjectName("livesetsSub")
            self.list_layout.addWidget(label)
            self.list_layout.addStretch(1)
            return
        for item in items:
            row = QFrame()
            row.setObjectName("liveRow")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(14, 10, 14, 10)
            title = QLabel(str(item.get("title") or "(geen titel)"))
            title.setObjectName("liveTitle")
            meta = QLabel(" • ".join(x for x in [str(item.get("artist") or ""), str(item.get("date") or ""), str(item.get("location") or "")] if x))
            meta.setObjectName("liveMeta")
            layout.addWidget(title)
            layout.addWidget(meta, 1)
            self.list_layout.addWidget(row)
        self.list_layout.addStretch(1)
