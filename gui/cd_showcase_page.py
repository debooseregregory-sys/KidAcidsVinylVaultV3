# ============================================================
# KID ACID'S VINYLVAULT V3
# CD SHOWCASE
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout,
)

from database.database import get_connection


class CDShowcasePage(QWidget):
    back_requested = Signal()
    release_selected = Signal(int)
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
        self.back_button = QPushButton("← CD LIBRARY")
        self.back_button.clicked.connect(self.back_requested.emit)
        top.addWidget(self.back_button)
        top.addStretch()
        root.addLayout(top)

        self.title_label = QLabel("CD SHOWCASE")
        self.title_label.setObjectName("showcaseTitle")
        root.addWidget(self.title_label)

        self.info_label = QLabel("Alle CD-releases")
        self.info_label.setObjectName("showcaseInfo")
        root.addWidget(self.info_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(10, 10, 10, 20)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(18)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet("""
            QWidget { background:#0b0b0f; color:#f5f5f7; font-family:'Segoe UI Semibold'; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a;
                border-radius:7px; padding:8px 14px; font-size:12px; font-weight:800; }
            QPushButton:hover { background:#24242c; border-color:#555563; }
            QLabel#showcaseTitle { color:#fff; font-size:26px; font-weight:900; }
            QLabel#showcaseInfo { color:#9b9ba6; font-size:13px; }
            QFrame#releaseCard { background:#121217; border:1px solid #292933; border-radius:10px; }
            QFrame#releaseCard:hover { border-color:#5b5b6b; }
            QLabel#cover { background:#07070a; color:#666671; border:1px solid #2a2a33; border-radius:6px; }
            QLabel#artist { color:#ffcf72; font-size:13px; font-weight:800; }
            QLabel#title { color:#fff; font-size:16px; font-weight:900; }
            QLabel#meta { color:#858591; font-size:12px; }
            QLabel#detailArtist { color:#ffcf72; font-size:20px; font-weight:900; }
            QLabel#detailTitle { color:#fff; font-size:32px; font-weight:900; }
            QLabel#section { color:#ffcf72; font-size:16px; font-weight:900; }
            QFrame#detailHero { background:#121217; border:1px solid #292933; border-radius:12px; }
            QFrame#metaCard { background:#101014; border:1px solid #292933; border-radius:9px; }
        """)

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_releases(self):
        self.release_id = None
        self._clear_grid()
        self.title_label.setText("CD SHOWCASE")
        self.back_button.setText("← CD LIBRARY")

        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, artist, title, label, catalog, year, genre, cover
                FROM cd_releases
                ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
                """
            ).fetchall()
        finally:
            conn.close()

        self.info_label.setText(f"{len(rows)} CD-releases")
        if not rows:
            self.grid.addWidget(QLabel("Geen CD-releases gevonden."), 0, 0)
            return

        columns = 5
        for index, row in enumerate(rows):
            self.grid.addWidget(self._create_card(row), index // columns, index % columns)
        for column in range(columns):
            self.grid.setColumnStretch(column, 1)

    def _create_card(self, row):
        card = QFrame()
        card.setObjectName("releaseCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setMinimumWidth(180)
        card.setMaximumWidth(260)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 12)
        layout.setSpacing(7)

        cover = QLabel("GEEN COVER")
        cover.setObjectName("cover")
        cover.setFixedSize(190, 190)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_path = str(row[7] or "").strip()
        if cover_path and Path(cover_path).exists():
            pix = QPixmap(cover_path)
            if not pix.isNull():
                cover.setPixmap(pix.scaled(190, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(cover, 0, Qt.AlignmentFlag.AlignHCenter)

        artist = QLabel(str(row[1] or "Onbekend"))
        artist.setObjectName("artist")
        artist.setWordWrap(True)
        layout.addWidget(artist)

        title = QLabel(str(row[2] or "(geen titel)"))
        title.setObjectName("title")
        title.setWordWrap(True)
        layout.addWidget(title)

        meta = [str(value) for value in (row[3], row[4], row[5]) if value]
        meta_label = QLabel(" • ".join(meta))
        meta_label.setObjectName("meta")
        meta_label.setWordWrap(True)
        layout.addWidget(meta_label)

        card.mousePressEvent = lambda event, rid=int(row[0]): self.release_selected.emit(rid)
        return card

    def _make_value_card(self, label, value):
        card = QFrame()
        card.setObjectName("metaCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        small = QLabel(label.upper())
        small.setObjectName("meta")
        text = QLabel(str(value or "—"))
        text.setObjectName("title")
        text.setWordWrap(True)
        layout.addWidget(small)
        layout.addWidget(text)
        return card

    def load_release(self, release_id):
        self.release_id = int(release_id)
        self._clear_grid()
        self.back_button.setText("← TERUG NAAR CD SHOWCASE")

        conn = get_connection()
        try:
            release = conn.execute(
                """
                SELECT id, artist, title, label, catalog, year, genre,
                       discogs, discogs_link, cover, notes, checked
                FROM cd_releases WHERE id = ?
                """,
                (self.release_id,),
            ).fetchone()
        finally:
            conn.close()

        if release is None:
            self.info_label.setText("CD niet gevonden")
            return

        artist = str(release[1] or "Onbekend")
        title = str(release[2] or "(geen titel)")
        self.title_label.setText("CD RELEASE")
        self.info_label.setText(f"{artist} — {title}")

        hero = QFrame()
        hero.setObjectName("detailHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(24)

        cover = QLabel("GEEN COVER")
        cover.setObjectName("cover")
        cover.setFixedSize(330, 330)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_path = str(release[9] or "").strip()
        if cover_path and Path(cover_path).exists():
            pix = QPixmap(cover_path)
            if not pix.isNull():
                cover.setPixmap(pix.scaled(330, 330, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hero_layout.addWidget(cover)

        info = QVBoxLayout()
        info.setSpacing(8)
        artist_label = QLabel(artist)
        artist_label.setObjectName("detailArtist")
        title_label = QLabel(title)
        title_label.setObjectName("detailTitle")
        title_label.setWordWrap(True)
        info.addWidget(artist_label)
        info.addWidget(title_label)

        if release[7]:
            discogs = QLabel(f"Discogs ID: {release[7]}")
            discogs.setObjectName("meta")
            info.addWidget(discogs)

        info.addSpacing(10)
        meta_grid = QGridLayout()
        fields = [
            ("LABEL", release[3]), ("CATALOGUS", release[4]),
            ("JAAR", release[5]), ("GENRE", release[6]),
        ]
        for index, (label, value) in enumerate(fields):
            meta_grid.addWidget(self._make_value_card(label, value), index // 2, index % 2)
        info.addLayout(meta_grid)

        if release[8]:
            discogs_button = QPushButton("OPEN DISCOGS")
            url = str(release[8])
            discogs_button.clicked.connect(lambda _checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            info.addWidget(discogs_button, 0, Qt.AlignmentFlag.AlignLeft)

        if release[10]:
            info.addSpacing(8)
            notes = QLabel(str(release[10]))
            notes.setObjectName("meta")
            notes.setWordWrap(True)
            info.addWidget(notes)

        info.addStretch()
        hero_layout.addLayout(info, 1)
        self.grid.addWidget(hero, 0, 0, 1, 2)

        section = QLabel("RELEASE-INFORMATIE")
        section.setObjectName("section")
        self.grid.addWidget(section, 1, 0, 1, 2)

        status = "GEKOPPELD" if int(release[11] or 0) else "NIET GEKOPPELD"
        self.grid.addWidget(self._make_value_card("STATUS", status), 2, 0)
        self.grid.addWidget(self._make_value_card("TYPE", "CD"), 2, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
