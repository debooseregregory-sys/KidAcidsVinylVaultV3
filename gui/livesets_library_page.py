from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"


class LivesetsLibraryPage(QWidget):
    """Livesets library entry point; editing is handled by the dedicated edit page."""
    showcase_requested = Signal()
    edit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.reload()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(10)
        title = QLabel("LIVESETS")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        line = QFrame()
        line.setObjectName("pageLine")
        line.setFixedHeight(2)
        line.setMaximumWidth(150)
        root.addWidget(line)
        root.addWidget(QLabel("Beheer je livesets of open de aparte Showcase."))

        actions = QHBoxLayout()
        library = QPushButton("✎  LIVESETS BEWERKEN")
        library.clicked.connect(self.edit_requested.emit)
        showcase = QPushButton("▶  LIVESETS SHOWCASE")
        showcase.clicked.connect(self.showcase_requested.emit)
        actions.addWidget(library)
        actions.addWidget(showcase)
        actions.addStretch(1)
        root.addLayout(actions)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:0;background:transparent;}")
        self.content = QWidget()
        self.list_layout = QVBoxLayout(self.content)
        self.list_layout.setContentsMargins(0, 8, 0, 20)
        self.list_layout.setSpacing(8)
        scroll.setWidget(self.content)
        root.addWidget(scroll, 1)

        self.setStyleSheet("""
            QLabel#pageTitle{color:#fff;font-size:26px;font-weight:900;}
            QFrame#pageLine{background:#ffcf72;border-radius:1px;}
            QLabel{color:#858591;font-size:13px;}
            QPushButton{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:7px;padding:10px 15px;font-size:11px;font-weight:900;}
            QPushButton:hover{background:#24242c;border-color:#ffcf72;}
            QFrame#liveRow{background:#121217;border:1px solid #292933;border-radius:8px;}
            QLabel#liveTitle{color:#fff;font-size:14px;font-weight:900;}
            QLabel#liveMeta{color:#858591;font-size:11px;}
        """)

    def reload(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError, json.JSONDecodeError):
            items = []
        if not items:
            self.list_layout.addWidget(QLabel("Nog geen livesets toegevoegd."))
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
