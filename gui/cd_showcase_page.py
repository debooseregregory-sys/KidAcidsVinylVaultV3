# ============================================================
# KID ACID'S VINYLVAULT V3
# CD SHOWCASE
# ============================================================

from pathlib import Path

import requests

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QLineEdit,
)

from database.database import get_connection
from database.cd_database import get_cd_tracks, save_cd_discogs_tracks
from tools.discogs import get_release


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
        self.back_button.clicked.connect(self._back_clicked)
        top.addWidget(self.back_button)
        top.addStretch()
        root.addLayout(top)

        self.title_label = QLabel("CD SHOWCASE")
        self.title_label.setObjectName("showcaseTitle")
        root.addWidget(self.title_label)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Zoek CD op artiest of titel...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._search_changed)
        search_row.addWidget(self.search_edit, 1)
        root.addLayout(search_row)

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
            QLineEdit { background:#121217; color:#fff; border:1px solid #30303a;
                border-radius:8px; padding:10px 12px; font-size:13px; }
            QLineEdit:focus { border-color:#5b5b6b; }
            QLabel#showcaseTitle { color:#fff; font-size:26px; font-weight:900; }
            QLabel#showcaseInfo { color:#9b9ba6; font-size:13px; }
            QFrame#releaseCard { background:#121217; border:1px solid #292933; border-radius:10px; }
            QFrame#releaseCard:hover { border-color:#5b5b6b; }
            QLabel#cover { background:#07070a; color:#666671; border:1px solid #2a2a33; border-radius:6px; }
            QLabel#artist { color:#ffcf72; font-size:13px; font-weight:800; }
            QLabel#title { color:#fff; font-size:16px; font-weight:900; }
            QLabel#meta { color:#858591; font-size:12px; }
            QLabel#detailArtist { color:#ffcf72; font-size:20px; font-weight:900; }
            QLabel#detailTitle { color:#fff; font-size:30px; font-weight:900; }
            QLabel#section { color:#ffcf72; font-size:16px; font-weight:900; }
            QFrame#detailHero { background:#121217; border:1px solid #292933; border-radius:12px; }
            QFrame#metaCard { background:#101014; border:1px solid #292933; border-radius:9px; }
            QFrame#trackRow { background:#101014; border:1px solid #292933; border-radius:7px; }
            QLabel#trackPosition { color:#ffcf72; font-size:12px; font-weight:900; }
            QLabel#trackTitle { color:#fff; font-size:14px; font-weight:800; }
            QLabel#trackArtist { color:#8f8f9a; font-size:12px; }
            QLabel#trackDuration { color:#aaaab4; font-size:12px; }
        """)

    def _back_clicked(self):
        if self.release_id is not None:
            self.release_id = None
            self.load_releases()
            return
        self.back_requested.emit()

    def _search_changed(self, text):
        if self.release_id is not None:
            return
        self.load_releases(text)

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _cover_cache_dir():
        cache_dir = Path(__file__).resolve().parent.parent / "data" / "cd_covers"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @classmethod
    def _cached_cover_path(cls, cover_value):
        cover_value = str(cover_value or "").strip()
        if not cover_value.lower().startswith(("http://", "https://")):
            return Path(cover_value) if cover_value else None
        return cls._cover_cache_dir() / f"{abs(hash(cover_value))}.jpg"

    @classmethod
    def _load_cover_pixmap(cls, cover_value):
        cover_value = str(cover_value or "").strip()
        if not cover_value:
            return QPixmap()
        if cover_value.lower().startswith(("http://", "https://")):
            cache_path = cls._cached_cover_path(cover_value)
            if cache_path and cache_path.exists():
                pix = QPixmap(str(cache_path))
                if not pix.isNull():
                    return pix
            try:
                response = requests.get(
                    cover_value,
                    timeout=10,
                    headers={"User-Agent": "KidAcidsVinylVaultV3/1.0"},
                )
                response.raise_for_status()
                pix = QPixmap()
                if pix.loadFromData(response.content):
                    try:
                        cache_path.write_bytes(response.content)
                    except OSError:
                        pass
                    return pix
            except Exception:
                return QPixmap()
            return QPixmap()
        path = Path(cover_value)
        if path.exists():
            pix = QPixmap(str(path))
            if not pix.isNull():
                return pix
        return QPixmap()

    def _set_cover(self, label, cover_value, size):
        pix = self._load_cover_pixmap(cover_value)
        if not pix.isNull():
            label.setPixmap(pix.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    def load_releases(self, search_text=""):
        self.release_id = None
        self._clear_grid()
        self.title_label.setText("CD SHOWCASE")
        self.back_button.setText("← CD LIBRARY")
        search_text = str(search_text or "").strip()
        conn = get_connection()
        try:
            if search_text:
                pattern = f"%{search_text}%"
                rows = conn.execute("""
                    SELECT id, artist, title, label, catalog, year, genre, cover
                    FROM cd_releases
                    WHERE artist LIKE ? COLLATE NOCASE OR title LIKE ? COLLATE NOCASE
                    ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
                """, (pattern, pattern)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, artist, title, label, catalog, year, genre, cover
                    FROM cd_releases
                    ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
                """).fetchall()
        finally:
            conn.close()
        self.info_label.setText(
            f"{len(rows)} resultaten voor ‘{search_text}’" if search_text else f"{len(rows)} CD-releases"
        )
        if not rows:
            message = f"Geen CD-releases gevonden voor ‘{search_text}’." if search_text else "Geen CD-releases gevonden."
            self.grid.addWidget(QLabel(message), 0, 0)
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
        self._set_cover(cover, row[7], 190)
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
        layout.setContentsMargins(12, 9, 12, 9)
        small = QLabel(label.upper())
        small.setObjectName("meta")
        text = QLabel(str(value or "—"))
        text.setObjectName("title")
        text.setWordWrap(True)
        layout.addWidget(small)
        layout.addWidget(text)
        return card

    def _make_track_row(self, track):
        row = QFrame()
        row.setObjectName("trackRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(12)
        position = QLabel(str(track[2] or ""))
        position.setObjectName("trackPosition")
        position.setFixedWidth(52)
        layout.addWidget(position)
        middle = QVBoxLayout()
        middle.setSpacing(2)
        title = QLabel(str(track[5] or "(geen titel)"))
        title.setObjectName("trackTitle")
        title.setWordWrap(True)
        middle.addWidget(title)
        artist = str(track[4] or "").strip()
        if artist:
            artist_label = QLabel(artist)
            artist_label.setObjectName("trackArtist")
            artist_label.setWordWrap(True)
            middle.addWidget(artist_label)
        layout.addLayout(middle, 1)
        duration = QLabel(str(track[6] or ""))
        duration.setObjectName("trackDuration")
        duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        duration.setFixedWidth(55)
        layout.addWidget(duration)
        mp3_path = str(track[8] or "").strip()
        if mp3_path:
            play_button = QPushButton("▶")
            play_button.setToolTip(f"Speel MP3: {Path(mp3_path).name}")
            play_button.setFixedSize(38, 32)
            play_button.clicked.connect(
                lambda _checked=False, path=mp3_path: self.play_mp3.emit(path)
            )
            layout.addWidget(play_button)
        else:
            no_mp3 = QLabel("GEEN MP3")
            no_mp3.setObjectName("meta")
            no_mp3.setFixedWidth(62)
            no_mp3.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(no_mp3)
        return row

    def load_release(self, release_id):
        self.release_id = int(release_id)
        self._clear_grid()
        self.back_button.setText("← TERUG NAAR CD SHOWCASE")
        conn = get_connection()
        try:
            release = conn.execute("""
                SELECT id, artist, title, label, catalog, year, genre,
                       discogs, discogs_link, cover, notes, checked
                FROM cd_releases WHERE id = ?
            """, (self.release_id,)).fetchone()
        finally:
            conn.close()
        if release is None:
            self.info_label.setText("CD niet gevonden")
            return
        tracks = get_cd_tracks(self.release_id)
        if not tracks and str(release[7] or "").strip().isdigit():
            try:
                discogs_release = get_release(str(release[7]).strip())
                save_cd_discogs_tracks(self.release_id, discogs_release)
                tracks = get_cd_tracks(self.release_id)
            except Exception as error:
                self.info_label.setText(
                    f"{release[1] or 'Onbekend'} — {release[2] or '(geen titel)'} | Discogs tracks niet geladen: {error}"
                )
        artist = str(release[1] or "Onbekend")
        title = str(release[2] or "(geen titel)")
        self.title_label.setText("CD RELEASE")
        self.info_label.setText(f"{artist} — {title}")
        hero = QFrame()
        hero.setObjectName("detailHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(12, 10, 12, 10)
        hero_layout.setSpacing(14)
        info = QVBoxLayout()
        info.setSpacing(7)
        artist_label = QLabel(artist)
        artist_label.setObjectName("detailArtist")
        info.addWidget(artist_label)
        title_label = QLabel(title)
        title_label.setObjectName("detailTitle")
        title_label.setWordWrap(True)
        info.addWidget(title_label)
        meta_grid = QGridLayout()
        meta_grid.setHorizontalSpacing(10)
        meta_grid.setVerticalSpacing(8)
        fields = [
            ("LABEL", release[3]), ("CATALOGUS", release[4]), ("JAAR", release[5]),
            ("GENRE", release[6]), ("TYPE", "CD"),
            ("STATUS", "GEKOPPELD" if int(release[11] or 0) else "NIET GEKOPPELD"),
        ]
        for index, (label, value) in enumerate(fields):
            meta_grid.addWidget(self._make_value_card(label, value), index // 3, index % 3)
        info.addLayout(meta_grid)
        if release[7]:
            discogs = QLabel(f"Discogs ID: {release[7]}")
            discogs.setObjectName("meta")
            info.addWidget(discogs)
        if release[8]:
            discogs_button = QPushButton("OPEN DISCOGS")
            url = str(release[8])
            discogs_button.clicked.connect(lambda _checked=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            info.addWidget(discogs_button, 0, Qt.AlignmentFlag.AlignLeft)
        if release[10]:
            notes = QLabel(str(release[10]))
            notes.setObjectName("meta")
            notes.setWordWrap(True)
            info.addWidget(notes)
        cover = QLabel("GEEN COVER")
        cover.setObjectName("cover")
        cover.setFixedSize(260, 260)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_cover(cover, release[9], 260)
        hero_layout.addLayout(info, 1)
        hero_layout.addWidget(cover, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.grid.addWidget(hero, 0, 0, 1, 2)
        section = QLabel(f"TRACKS  •  {len(tracks)}")
        section.setObjectName("section")
        self.grid.addWidget(section, 1, 0, 1, 2)
        if tracks:
            for index, track in enumerate(tracks, start=2):
                self.grid.addWidget(self._make_track_row(track), index, 0, 1, 2)
        else:
            placeholder = QLabel("Geen tracks gekoppeld. Deze CD heeft nog geen Discogs Release ID.")
            placeholder.setObjectName("meta")
            placeholder.setWordWrap(True)
            self.grid.addWidget(placeholder, 2, 0, 1, 2)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
