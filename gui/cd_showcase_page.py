# ============================================================
# KID ACID'S VINYLVAULT V3
# CD SHOWCASE
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)

from database.database import get_connection


class CDShowcasePage(QWidget):
    back_requested = Signal()
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.release_id = None
        self.build_ui()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        back = QPushButton("← TERUG NAAR CD LIBRARY")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        top.addStretch()
        root.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 20)
        self.content_layout.setSpacing(16)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet("""
            QWidget { background:#0b0b0f; color:#f5f5f7; font-family:'Segoe UI Semibold'; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a;
                border-radius:7px; padding:8px 14px; font-size:12px; font-weight:800; }
            QPushButton:hover { background:#24242c; border-color:#555563; }
            QLabel#artist { color:#ffcf72; font-size:18px; font-weight:800; }
            QLabel#title { color:#fff; font-size:30px; font-weight:900; }
            QLabel#meta { color:#9b9ba6; font-size:13px; }
            QLabel#cover { background:#07070a; color:#666671; border:1px solid #2a2a33; border-radius:8px; }
            QFrame#card { background:#121217; border:1px solid #292933; border-radius:10px; }
        """)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_release(self, release_id):
        self.release_id = int(release_id)
        self._clear()

        conn = get_connection()
        try:
            release = conn.execute(
                """
                SELECT id, artist, title, label, catalog, year, genre,
                       discogs, discogs_link, cover, notes, checked
                FROM cd_releases
                WHERE id = ?
                """,
                (self.release_id,),
            ).fetchone()
        finally:
            conn.close()

        if release is None:
            self.content_layout.addWidget(QLabel("CD niet gevonden"))
            return

        artist = str(release[1] or "Onbekend")
        title = str(release[2] or "(geen titel)")
        cover_path = str(release[9] or "").strip()

        hero = QFrame()
        hero.setObjectName("card")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(22)

        cover = QLabel("GEEN COVER")
        cover.setObjectName("cover")
        cover.setFixedSize(320, 320)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if cover_path and Path(cover_path).exists():
            pix = QPixmap(cover_path)
            if not pix.isNull():
                cover.setPixmap(pix.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hero_layout.addWidget(cover)

        info = QVBoxLayout()
        artist_label = QLabel(artist)
        artist_label.setObjectName("artist")
        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setWordWrap(True)
        info.addWidget(artist_label)
        info.addWidget(title_label)

        meta = []
        if release[3]: meta.append(str(release[3]))
        if release[4]: meta.append(str(release[4]))
        if release[5]: meta.append(str(release[5]))
        if release[6]: meta.append(str(release[6]))
        meta_label = QLabel(" • ".join(meta) if meta else "CD")
        meta_label.setObjectName("meta")
        meta_label.setWordWrap(True)
        info.addWidget(meta_label)

        if release[7]:
            discogs_label = QLabel(f"Discogs: {release[7]}")
            discogs_label.setObjectName("meta")
            info.addWidget(discogs_label)
        if release[8]:
            button = QPushButton("OPEN DISCOGS")
            url = str(release[8])
            button.clicked.connect(lambda _checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            info.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)

        if release[10]:
            notes = QLabel(str(release[10]))
            notes.setObjectName("meta")
            notes.setWordWrap(True)
            info.addSpacing(12)
            info.addWidget(notes)

        info.addStretch()
        hero_layout.addLayout(info, 1)
        self.content_layout.addWidget(hero)

        status = QLabel("CD RELEASE")
        status.setObjectName("artist")
        self.content_layout.addWidget(status)
        self.content_layout.addStretch()
