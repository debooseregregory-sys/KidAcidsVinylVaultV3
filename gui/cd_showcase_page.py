# ============================================================
# KID ACID'S VINYLVAULT V3
# CD SHOWCASE
#
# Shows the complete CD collection, like the Vinyl Showcase.
# Clicking a CD opens its detailed view.
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
        back = QPushButton("← CD LIBRARY")
        back.clicked.connect(self.back_requested.emit)
        top.addWidget(back)
        top.addStretch()
        root.addLayout(top)

        title = QLabel("CD SHOWCASE")
        title.setObjectName("showcaseTitle")
        root.addWidget(title)

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
            QLabel#artist { color:#ffcf72; font-size:12px; font-weight:800; }
            QLabel#title { color:#fff; font-size:14px; font-weight:900; }
            QLabel#meta { color:#858591; font-size:11px; }
        """)

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_releases(self):
        """Load and display every CD release from cd_releases."""
        self.release_id = None
        self._clear_grid()

        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, artist, title, label, catalog, year, genre, cover
                FROM cd_releases
                ORDER BY artist COLLATE NOCASE,
                         title COLLATE NOCASE,
                         id
                """
            ).fetchall()
        finally:
            conn.close()

        self.info_label.setText(f"{len(rows)} CD-releases")

        if not rows:
            empty = QLabel("Geen CD-releases gevonden.")
            empty.setObjectName("showcaseInfo")
            self.grid.addWidget(empty, 0, 0)
            return

        columns = 5
        for index, row in enumerate(rows):
            card = self._create_card(row)
            self.grid.addWidget(card, index // columns, index % columns)

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
                cover.setPixmap(
                    pix.scaled(
                        190, 190,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        layout.addWidget(cover, 0, Qt.AlignmentFlag.AlignHCenter)

        artist = QLabel(str(row[1] or "Onbekend"))
        artist.setObjectName("artist")
        artist.setWordWrap(True)
        layout.addWidget(artist)

        title = QLabel(str(row[2] or "(geen titel)"))
        title.setObjectName("title")
        title.setWordWrap(True)
        layout.addWidget(title)

        meta = []
        if row[3]:
            meta.append(str(row[3]))
        if row[4]:
            meta.append(str(row[4]))
        if row[5]:
            meta.append(str(row[5]))
        meta_label = QLabel(" • ".join(meta))
        meta_label.setObjectName("meta")
        meta_label.setWordWrap(True)
        layout.addWidget(meta_label)

        card.mousePressEvent = lambda event, rid=int(row[0]): self.release_selected.emit(rid)
        return card

    def load_release(self, release_id):
        """Compatibility method: show one CD in a detail view."""
        self.release_id = int(release_id)
        self._clear_grid()

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
            self.info_label.setText("CD niet gevonden")
            return

        card = QFrame()
        card.setObjectName("releaseCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        cover = QLabel("GEEN COVER")
        cover.setObjectName("cover")
        cover.setFixedSize(320, 320)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover_path = str(release[9] or "").strip()
        if cover_path and Path(cover_path).exists():
            pix = QPixmap(cover_path)
            if not pix.isNull():
                cover.setPixmap(pix.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(cover, 0, Qt.AlignmentFlag.AlignHCenter)

        artist = QLabel(str(release[1] or "Onbekend"))
        artist.setObjectName("artist")
        layout.addWidget(artist)

        title = QLabel(str(release[2] or "(geen titel)"))
        title.setObjectName("title")
        title.setWordWrap(True)
        layout.addWidget(title)

        meta = []
        for value in (release[3], release[4], release[5], release[6]):
            if value:
                meta.append(str(value))
        meta_label = QLabel(" • ".join(meta) if meta else "CD")
        meta_label.setObjectName("meta")
        layout.addWidget(meta_label)

        if release[7]:
            discogs = QLabel(f"Discogs: {release[7]}")
            discogs.setObjectName("meta")
            layout.addWidget(discogs)

        if release[8]:
            button = QPushButton("OPEN DISCOGS")
            url = str(release[8])
            button.clicked.connect(lambda _checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)

        if release[10]:
            notes = QLabel(str(release[10]))
            notes.setObjectName("meta")
            notes.setWordWrap(True)
            layout.addWidget(notes)

        self.info_label.setText(f"{release[1] or 'Onbekend'} — {release[2] or '(geen titel)'}")
        self.grid.addWidget(card, 0, 0)
        self.grid.setColumnStretch(0, 1)
