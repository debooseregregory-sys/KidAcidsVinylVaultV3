from pathlib import Path
import urllib.request
import re

from PySide6.QtCore import Qt, QTimer, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableView, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QTextEdit,
)

from database.database import get_connection
from gui.mp3_duplicate_cleaner import MP3DuplicateCleaner
from gui.discogs_mp3_lookup import (
    parse_filename,
    search_releases,
    get_release,
    artist_names,
    label_info,
    genre_text,
    release_format,
    composer_text,
)

try:
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TBPM, TRCK, TPOS, TCOM, TPE2, COMM
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


# MP3 metadata progress helper
def ensure_mp3_metadata_progress():
    conn = get_connection()
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        if "metadata_checked" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked INTEGER NOT NULL DEFAULT 0")
        if "metadata_checked_at" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked_at TEXT")
        if "discogs_id" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN discogs_id TEXT")
        if "discogs_link" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN discogs_link TEXT")
        if "cover" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN cover TEXT")
        if "album_artist" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN album_artist TEXT")
        if "composer" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN composer TEXT")
        if "track" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN track TEXT")
        if "disc" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN disc TEXT")
        conn.commit()
    finally:
        conn.close()


def ensure_mp3_discogs_columns():
    conn = get_connection()
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        additions = {
            "discogs_id": "TEXT",
            "discogs_link": "TEXT",
            "cover": "TEXT",
        }
        for name, kind in additions.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}")
        conn.commit()
    finally:
        conn.close()


ROOT = Path(__file__).resolve().parents[1]


class MP3TableModel(QAbstractTableModel):
    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling", "Metadata"]

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self.rows = rows or []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.rows):
            return None
        row = self.rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return str(row[index.column()] or "")
        if role == Qt.ItemDataRole.BackgroundRole and int(row[9] or 0) == 1:
            from PySide6.QtGui import QColor
            return QColor("#4a3d08")
        if role == Qt.ItemDataRole.ForegroundRole and int(row[9] or 0) == 1:
            from PySide6.QtGui import QColor
            return QColor("#ffe08a")
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(row[8] or "") if index.column() == 5 else None
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class MetadataDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.path = str(row[0] or "")
        self.release = None
        self.setWindowTitle("MP3 Metadata Builder")
        self.resize(760, 680)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        tags = self.read_real_tags(self.path)
        filename = parse_filename(self.path)

        # Real ID3 tags win. When absent, filename parsing supplies a
        # suggestion, exactly as requested for poorly tagged files.
        artist = tags["artist"] or filename["artist"]
        title = tags["title"] or filename["title"]
        track = tags["track"] or filename["track"]

        self.artist = QLineEdit(artist)
        self.title = QLineEdit(title)
        self.album = QLineEdit(tags["album"])
        self.year = QLineEdit(tags["year"])
        self.bpm = QLineEdit(tags["bpm"])
        self.track = QLineEdit(track)
        self.disc = QLineEdit(tags["disc"])
        self.album_artist = QLineEdit(tags["album_artist"])
        self.composer = QLineEdit(tags["composer"])
        self.genre = QLineEdit(tags["genre"])
        self.comment = QTextEdit(tags["comment"])
        self.comment.setFixedHeight(75)

        form.addRow("Artist:", self.artist)
        form.addRow("Title:", self.title)
        form.addRow("Album:", self.album)
        form.addRow("Year:", self.year)
        form.addRow("BPM:", self.bpm)
        form.addRow("Track:", self.track)
        form.addRow("Disc:", self.disc)
        form.addRow("Album Artist:", self.album_artist)
        form.addRow("Composer:", self.composer)
        form.addRow("Genre:", self.genre)
        form.addRow("Comment:", self.comment)
        layout.addLayout(form)

        lookup_row = QHBoxLayout()
        self.discogs_search_button = QPushButton("[ DISCOGS ZOEKEN ]")
        self.discogs_search_button.clicked.connect(self.search_discogs)
        lookup_row.addWidget(self.discogs_search_button)

        self.discogs_candidates = QComboBox()
        self.discogs_candidates.setMinimumWidth(440)
        lookup_row.addWidget(self.discogs_candidates, 1)

        self.discogs_select_button = QPushButton("[ RELEASE KIEZEN ]")
        self.discogs_select_button.clicked.connect(self.select_discogs_release)
        lookup_row.addWidget(self.discogs_select_button)
        layout.addLayout(lookup_row)

        # HANDMATISCHE DISCOGS RELEASE
        manual_row = QHBoxLayout()

        manual_row.addWidget(
            QLabel("Discogs ID/link:")
        )

        self.manual_discogs_input = QLineEdit()
        self.manual_discogs_input.setPlaceholderText(
            "Release-ID of volledige Discogs release-link"
        )

        manual_row.addWidget(
            self.manual_discogs_input,
            1
        )

        self.manual_discogs_button = QPushButton(
            "[ HANDMATIG OPHALEN ]"
        )

        self.manual_discogs_button.clicked.connect(
            self.fetch_manual_discogs_release
        )

        manual_row.addWidget(
            self.manual_discogs_button
        )

        layout.addLayout(
            manual_row
        )

        self.track_choice = QComboBox()
        self.track_choice.setMinimumWidth(440)
        self.track_choice.currentIndexChanged.connect(self.apply_discogs_track)
        track_row = QHBoxLayout()
        track_row.addWidget(QLabel("Discogs track:"))
        track_row.addWidget(self.track_choice, 1)
        layout.addLayout(track_row)

        self.discogs_info = QLabel("Nog geen Discogs-resultaat geselecteerd.")
        self.discogs_info.setWordWrap(True)
        self.discogs_info.setStyleSheet("color:#9b9ba6; padding:6px 0;")
        layout.addWidget(self.discogs_info)

        self.status = QLabel(f"Bestand: {self.path}")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color:#777784; font-size:11px;")
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Save
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.restore_saved_discogs()

    @staticmethod
    def _frame_text(tags, key):
        frame = tags.get(key)
        if frame is None:
            return ""
        try:
            values = getattr(frame, "text", None)
            if values:
                return str(values[0]).strip()
        except Exception:
            pass
        return str(frame).strip()

    @classmethod
    def read_real_tags(cls, path):
        result = {
            "artist": "", "title": "", "album": "", "year": "",
            "bpm": "", "track": "", "disc": "", "album_artist": "",
            "composer": "", "genre": "", "comment": "",
        }

        if not MUTAGEN_AVAILABLE or not Path(path).exists():
            return result

        try:
            try:
                tags = ID3(path)
            except ID3NoHeaderError:
                return result

            result["artist"] = cls._frame_text(tags, "TPE1")
            result["title"] = cls._frame_text(tags, "TIT2")
            result["album"] = cls._frame_text(tags, "TALB")
            result["year"] = cls._frame_text(tags, "TDRC")
            result["bpm"] = cls._frame_text(tags, "TBPM")
            result["track"] = cls._frame_text(tags, "TRCK")
            result["disc"] = cls._frame_text(tags, "TPOS")
            result["album_artist"] = cls._frame_text(tags, "TPE2")
            result["composer"] = cls._frame_text(tags, "TCOM")
            result["genre"] = cls._frame_text(tags, "TCON")

            comments = tags.getall("COMM")
            values = []
            for frame in comments:
                try:
                    values.extend(
                        str(value).strip()
                        for value in frame.text
                        if str(value).strip()
                    )
                except Exception:
                    pass
            result["comment"] = " | ".join(dict.fromkeys(values))
        except Exception:
            pass

        return result
    def restore_saved_discogs(self):
        """
        Herlaad een eerder opgeslagen Discogs-release wanneer
        de MetadataDialog opnieuw geopend wordt.
        """
        try:
            conn = get_connection()

            try:
                row = conn.execute(
                    """
                    SELECT
                        discogs_id,
                        discogs_link,
                        cover
                    FROM mp3_files
                    WHERE path = ?
                    LIMIT 1
                    """,
                    (self.path,),
                ).fetchone()

            finally:
                conn.close()

        except Exception:
            return

        if not row:
            return

        discogs_id = str(
            row[0] or ""
        ).strip()

        discogs_link = str(
            row[1] or ""
        ).strip()

        cover = str(
            row[2] or ""
        ).strip()

        if not discogs_id:
            return

        try:
            self.release = get_release(
                int(discogs_id)
            )
        except Exception:
            self.release = None

            if hasattr(self, "discogs_info"):
                self.discogs_info.setText(
                    f"Discogs opgeslagen: {discogs_id}, "
                    "maar de release kon niet opnieuw worden opgehaald."
                )

            return

        release_artist = artist_names(
            self.release
        )

        release_title = str(
            self.release.get("title") or ""
        ).strip()

        release_year = str(
            self.release.get("year") or ""
        ).strip()

        self.artist.setText(
            release_artist
        )

        self.album_artist.setText(
            release_artist
        )

        self.album.setText(
            release_title
        )

        if release_year:
            self.year.setText(
                release_year
            )

        genre = genre_text(
            self.release
        )

        if genre:
            self.genre.setText(
                genre
            )

        tracks = self.release.get(
            "tracklist"
        ) or []

        self.track_choice.blockSignals(
            True
        )

        self.track_choice.clear()

        for index, track in enumerate(tracks):

            if not isinstance(track, dict):
                continue

            title = str(
                track.get("title") or ""
            ).strip()

            if not title:
                continue

            position = str(
                track.get("position") or ""
            ).strip()

            duration = str(
                track.get("duration") or ""
            ).strip()

            label = (
                f"{position} | {title}"
            )

            if duration:
                label += (
                    f" | {duration}"
                )

            self.track_choice.addItem(
                label,
                index
            )

        self.track_choice.blockSignals(
            False
        )

        # Probe tracks opnieuw en vul de beste match in.
        self._choose_best_track()
        self.apply_discogs_track()

        # Bestaande handmatige Discogs-invoer terugzetten
        # als die in de huidige editor bestaat.
        if hasattr(
            self,
            "manual_discogs_input"
        ):
            self.manual_discogs_input.setText(
                discogs_link
                or f"https://www.discogs.com/release/{discogs_id}"
            )

        if hasattr(
            self,
            "discogs_info"
        ):
            self.discogs_info.setText(
                f"✓ OPGEHAALD EN OPGESLAGEN | "
                f"Discogs {discogs_id} | "
                f"{release_artist} — "
                f"{release_title} | "
                f"{release_year}"
            )

        # Coverpad uit database terugzetten wanneer
        # de editor daar een coverveld voor heeft.
        if cover and hasattr(
            self,
            "edit_cover"
        ):
            self.edit_cover.setText(
                cover
            )

    @staticmethod
    def _candidate_text(result):
        title = str(result.get("title") or "").strip()
        year = str(result.get("year") or "").strip()
        fmt = ", ".join(str(x) for x in (result.get("format") or []) if x)
        label = str(result.get("label") or "").strip()
        catno = str(result.get("catno") or "").strip()
        extra = " | ".join(
            x for x in (
                year,
                fmt,
                label + (f" [{catno}]" if catno else ""),
            ) if x
        )
        return f"[{result.get('id', '')}] {title}" + (f" | {extra}" if extra else "")

    def search_discogs(self):
        artist = self.artist.text().strip()
        title = self.title.text().strip()
        if not artist and not title:
            QMessageBox.information(
                self,
                "Discogs",
                "Vul minstens artiest of titel in, of gebruik een bestandsnaam waaruit dit afgeleid kan worden.",
            )
            return

        try:
            results = search_releases(artist, title, limit=10)
        except Exception as exc:
            QMessageBox.critical(self, "Discogs zoeken mislukt", str(exc))
            return

        self.discogs_candidates.clear()
        for result in results:
            self.discogs_candidates.addItem(
                self._candidate_text(result),
                result.get("id")
            )

        if results:
            self.discogs_info.setText(
                f"{len(results)} Discogs releases gevonden. Kies eerst de juiste release."
            )
        else:
            self.discogs_info.setText("Geen Discogs releases gevonden.")

    def select_discogs_release(self):
        release_id = self.discogs_candidates.currentData()
        if not release_id:
            QMessageBox.information(self, "Discogs", "Kies eerst een release uit de lijst.")
            return

        try:
            self.release = get_release(release_id)
        except Exception as exc:
            QMessageBox.critical(self, "Discogs release ophalen mislukt", str(exc))
            return

        release_artist = artist_names(self.release)
        self.artist.setText(release_artist)
        self.album_artist.setText(release_artist)
        self.album.setText(str(self.release.get("title") or "").strip())
        self.year.setText(str(self.release.get("year") or ""))
        self.genre.setText(genre_text(self.release))

        tracks = self.release.get("tracklist") or []
        self.track_choice.blockSignals(True)
        self.track_choice.clear()
        for index, track in enumerate(tracks):
            if not isinstance(track, dict):
                continue
            position = str(track.get("position") or "").strip()
            title = str(track.get("title") or "").strip()
            duration = str(track.get("duration") or "").strip()
            if not title:
                continue
            text = f"{position} | {title}" + (f" | {duration}" if duration else "")
            self.track_choice.addItem(text, index)
        self.track_choice.blockSignals(False)

        self.discogs_info.setText(
            f"Discogs {release_id} | {self.release.get('title', '')} | "
            f"{self.release.get('year') or ''} | "
            f"{release_format(self.release)} | {label_info(self.release)}"
        )

        # Automatically use the best matching track where possible.
        self._choose_best_track()
        self.apply_discogs_track()

    def fetch_manual_discogs_release(self):
        value = self.manual_discogs_input.text().strip()

        if not value:
            QMessageBox.information(
                self,
                "Discogs",
                "Vul een Discogs release-ID of volledige release-link in."
            )
            return

        match = re.search(
            r"/release/(\d+)|^(\d+)$",
            value
        )

        if not match:
            QMessageBox.warning(
                self,
                "Discogs",
                "Geen geldig Discogs release-ID gevonden."
            )
            return

        release_id = int(
            match.group(1) or match.group(2)
        )

        try:
            self.release = get_release(
                release_id
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Discogs release ophalen mislukt",
                str(exc)
            )
            return

        release_artist = artist_names(
            self.release
        )

        self.artist.setText(
            release_artist
        )

        self.album_artist.setText(
            release_artist
        )

        self.album.setText(
            str(
                self.release.get("title") or ""
            ).strip()
        )

        self.year.setText(
            str(
                self.release.get("year") or ""
            )
        )

        self.genre.setText(
            genre_text(self.release)
        )

        tracks = self.release.get(
            "tracklist"
        ) or []

        self.track_choice.blockSignals(True)
        self.track_choice.clear()

        for index, track in enumerate(tracks):

            if not isinstance(track, dict):
                continue

            title = str(
                track.get("title") or ""
            ).strip()

            if not title:
                continue

            position = str(
                track.get("position") or ""
            ).strip()

            duration = str(
                track.get("duration") or ""
            ).strip()

            label = f"{position} | {title}"

            if duration:
                label += f" | {duration}"

            self.track_choice.addItem(
                label,
                index
            )

        self.track_choice.blockSignals(False)

        self._choose_best_track()
        self.apply_discogs_track()

        self.discogs_info.setText(
            f"Handmatig geladen: Discogs {release_id} | "
            f"{self.release.get('title', '')} | "
            f"{self.release.get('year') or ''} | "
            f"{release_format(self.release)} | "
            f"{label_info(self.release)}"
        )

    def _choose_best_track(self):
        wanted = self.title.text().strip().casefold()
        if not wanted or self.track_choice.count() == 0:
            return
        best_index = 0
        best_score = 0
        for i in range(self.track_choice.count()):
            label = self.track_choice.itemText(i).casefold()
            score = 100 if wanted in label else 0
            if score > best_score:
                best_score = score
                best_index = i
        self.track_choice.setCurrentIndex(best_index)

    def apply_discogs_track(self, *_args):
        if not self.release or self.track_choice.count() == 0:
            return

        wanted_index = self.track_choice.currentData()
        if wanted_index is None:
            return

        tracks = self.release.get("tracklist") or []
        valid_tracks = [x for x in tracks if isinstance(x, dict) and str(x.get("title") or "").strip()]
        if not 0 <= int(wanted_index) < len(valid_tracks):
            return

        track = valid_tracks[int(wanted_index)]
        self.title.setText(str(track.get("title") or "").strip())
        self.track.setText(str(track.get("position") or "").strip())

        composer = composer_text(self.release, track)
        if composer:
            self.composer.setText(composer)

        artists = []
        for artist in track.get("artists") or []:
            if isinstance(artist, dict) and artist.get("name"):
                artists.append(str(artist["name"]).strip())
        if artists:
            self.artist.setText(", ".join(dict.fromkeys(artists)))

    def persist_discogs_release(self, conn, path):
        # Ensure required columns exist even when an older DB is opened.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        for name, definition in {
            "discogs_id": "TEXT",
            "discogs_link": "TEXT",
            "cover": "TEXT",
            "album_artist": "TEXT",
            "composer": "TEXT",
            "track": "TEXT",
            "disc": "TEXT",
        }.items():
            if name not in existing:
                conn.execute(
                    f"ALTER TABLE mp3_files ADD COLUMN {name} {definition}"
                )

        release = getattr(self, "release", None)
        if not release:
            return

        release_id = str(release.get("id") or "").strip()
        release_link = (
            f"https://www.discogs.com/release/{release_id}"
            if release_id else ""
        )

        cover_path = ""
        images = release.get("images") or []
        if images:
            image_url = str(
                images[0].get("uri")
                or images[0].get("uri150")
                or ""
            ).strip()
            if image_url and release_id:
                covers_dir = ROOT / "covers"
                covers_dir.mkdir(exist_ok=True)
                target = covers_dir / f"mp3_release_{release_id}.jpg"
                try:
                    if not target.exists():
                        request = urllib.request.Request(
                            image_url,
                            headers={"User-Agent": "KidAcidsVinylVault/3.0"},
                        )
                        with urllib.request.urlopen(request, timeout=20) as response:
                            target.write_bytes(response.read())
                    if target.exists() and target.stat().st_size > 0:
                        cover_path = str(target)
                except Exception:
                    pass

        conn.execute(
            """
            UPDATE mp3_files
            SET discogs_id=?, discogs_link=?, cover=?,
                album_artist=?, composer=?, track=?, disc=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE path=?
            """,
            (
                release_id,
                release_link,
                cover_path,
                str(self.album_artist.text()).strip(),
                str(self.composer.text()).strip(),
                str(self.track.text()).strip(),
                str(self.disc.text()).strip(),
                path,
            ),
        )

    def save(self):
        path = str(self.row[0] or "")
        if not MUTAGEN_AVAILABLE:
            QMessageBox.warning(
                self,
                "Mutagen ontbreekt",
                "Installeer eerst Mutagen:\n\npython -m pip install mutagen",
            )
            return

        if not Path(self.path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", self.path)
            return

        try:
            try:
                tags = ID3(self.path)
            except ID3NoHeaderError:
                tags = ID3()

            def text(value):
                return str(value).strip()

            mapping = {
                "TPE1": text(self.artist.text()),
                "TIT2": text(self.title.text()),
                "TALB": text(self.album.text()),
                "TDRC": text(self.year.text()),
                "TBPM": text(self.bpm.text()),
                "TRCK": text(self.track.text()),
                "TPOS": text(self.disc.text()),
                "TPE2": text(self.album_artist.text()),
                "TCOM": text(self.composer.text()),
                "TCON": text(self.genre.text()),
            }

            tags.delall("TPE1")
            if mapping["TPE1"]:
                tags.add(TPE1(encoding=3, text=mapping["TPE1"]))
            tags.delall("TIT2")
            if mapping["TIT2"]:
                tags.add(TIT2(encoding=3, text=mapping["TIT2"]))
            tags.delall("TALB")
            if mapping["TALB"]:
                tags.add(TALB(encoding=3, text=mapping["TALB"]))
            tags.delall("TCON")
            if mapping["TCON"]:
                tags.add(TCON(encoding=3, text=mapping["TCON"]))
            tags.delall("TDRC")
            if mapping["TDRC"]:
                tags.add(TDRC(encoding=3, text=mapping["TDRC"]))
            tags.delall("TBPM")
            if mapping["TBPM"]:
                from mutagen.id3 import TBPM
                tags.add(TBPM(encoding=3, text=mapping["TBPM"]))
            tags.delall("TRCK")
            if mapping["TRCK"]:
                tags.add(TRCK(encoding=3, text=mapping["TRCK"]))
            tags.delall("TPOS")
            if mapping["TPOS"]:
                tags.add(TPOS(encoding=3, text=mapping["TPOS"]))
            tags.delall("TPE2")
            if mapping["TPE2"]:
                tags.add(TPE2(encoding=3, text=mapping["TPE2"]))
            tags.delall("TCOM")
            if mapping["TCOM"]:
                tags.add(TCOM(encoding=3, text=mapping["TCOM"]))
            tags.delall("COMM")
            comment_text = text(self.comment.toPlainText())
            if comment_text:
                tags.add(COMM(encoding=3, lang="eng", desc="", text=comment_text))

            tags.save(self.path, v2_version=3)

            db_year = int(mapping["TDRC"]) if mapping["TDRC"].isdigit() else None
            try:
                db_bpm = float(mapping["TBPM"]) if mapping["TBPM"] else None
            except ValueError:
                db_bpm = None

            conn = get_connection()
            try:
                conn.execute(
                    """
                    UPDATE mp3_files
                    SET artist=?, title=?, album=?, year=?, genre=?, bpm=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE path=?
                    """,
                    (
                        mapping["TPE1"],
                        mapping["TIT2"],
                        mapping["TALB"],
                        db_year,
                        mapping["TCON"],
                        db_bpm,
                        self.path,
                    ),
                )
                conn.execute(
                    "UPDATE mp3_files SET metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP WHERE path=?",
                    (path,),
                )
                self.persist_discogs_release(conn, path)
                conn.commit()
            finally:
                conn.close()

            

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Metadata opslaan mislukt", str(exc))


class MP3LibraryPage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.filtered_rows = []
        self.metadata_status_by_path = {}
        self.metadata_mode = "all"
        ensure_mp3_metadata_progress()
        ensure_mp3_discogs_columns()
        self.build_ui()
        self.load_data()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(12)

        title = QLabel("MP3 LIBRARY")
        title.setStyleSheet("font-size: 25px; font-weight: 900; color: #ffffff;")
        root.addWidget(title)

        tools = QHBoxLayout()
        tools.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, bestandsnaam…")
        tools.addWidget(self.search, 1)

        self.filter = QComboBox()
        self.filter.addItems([
            "Alle MP3's",
            "Aan vinyl gekoppeld",
            "Niet gekoppeld",
        ])
        tools.addWidget(self.filter)

        self.all_button = QPushButton("ALLES")
        self.done_button = QPushButton("✓ KLAAR")
        self.todo_button = QPushButton("NIET GEDAAN")
        tools.addWidget(self.all_button)
        tools.addWidget(self.done_button)
        tools.addWidget(self.todo_button)

        self.refresh = QPushButton("VERVERS")
        tools.addWidget(self.refresh)
        root.addLayout(tools)

        self.progress_label = QLabel("Metadata: 0 KLAAR | 0 NIET GEDAAN | 0 TOTAAL")
        self.progress_label.setStyleSheet(
            "color: #b5a9bd; font-size: 13px; font-weight: bold;"
        )
        root.addWidget(self.progress_label)

        self.info = QLabel("0 MP3's")
        self.info.setStyleSheet("color: #9b9ba6;")
        root.addWidget(self.info)

        self.table = QTableView()
        self.model = MP3TableModel(parent=self.table)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(False)
        self.table.doubleClicked.connect(self.play_selected)
        self.table.setColumnWidth(0, 190)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 220)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 75)
        self.table.setColumnWidth(5, 320)
        self.table.setColumnWidth(6, 90)
        self.table.setColumnWidth(7, 120)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 8, 0, 0)
        actions.setSpacing(10)

        self.play_button = QPushButton("▶ PLAY")
        self.meta_button = QPushButton("METADATA BEWERKEN")
        self.duplicates_button = QPushButton("DUBBELE MP3'S")
        actions.addWidget(self.duplicates_button)
        self.open_folder_button = QPushButton("OPEN MAP")

        actions.addWidget(self.play_button)
        actions.addWidget(self.meta_button)
        actions.addWidget(self.open_folder_button)
        actions.addStretch()
        root.addLayout(actions)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.apply_filter)
        self.search.textChanged.connect(lambda _: self.search_timer.start())
        self.filter.currentIndexChanged.connect(self.apply_filter)
        self.all_button.clicked.connect(lambda: self.set_metadata_mode("all"))
        self.done_button.clicked.connect(lambda: self.set_metadata_mode("done"))
        self.todo_button.clicked.connect(lambda: self.set_metadata_mode("todo"))
        self.refresh.clicked.connect(self.load_data)
        self.play_button.clicked.connect(self.play_selected)
        self.meta_button.clicked.connect(self.edit_selected_metadata)
        self.duplicates_button.clicked.connect(self.open_duplicate_cleaner)
        self.open_folder_button.clicked.connect(self.open_selected_folder)

        self.setStyleSheet("""
            QWidget {
                background: #0b0b0f;
                color: #f2f2f5;
            }
            QLineEdit, QComboBox, QPushButton {
                background: #18181f;
                color: #fff;
                border: 1px solid #30303a;
                border-radius: 6px;
                padding: 8px 10px;
            }
            QPushButton:hover {
                border-color: #d84b91;
                background: #24242c;
            }
            QTableView {
                background: #0f0f14;
                border: 1px solid #25252d;
                gridline-color: #202028;
            }
            QTableView::item {
                padding: 6px;
            }
            QHeaderView::section {
                background: #18181f;
                color: #aaaaaf;
                padding: 7px;
                border: none;
            }
        """)

        self._update_status_button_style()

    def _update_status_button_style(self):
        active = "background:#4a3d08; color:#ffe08a; border:1px solid #8e7620;"
        normal = "background:#18181f; color:#fff; border:1px solid #30303a;"

        for button, mode in (
            (self.all_button, "all"),
            (self.done_button, "done"),
            (self.todo_button, "todo"),
        ):
            if self.metadata_mode == mode:
                button.setStyleSheet(
                    f"QPushButton {{ {active} border-radius:6px; padding:8px 10px; font-weight:bold; }}"
                )
            else:
                button.setStyleSheet(
                    f"QPushButton {{ {normal} border-radius:6px; padding:8px 10px; }}"
                )

    def set_metadata_mode(self, mode):
        self.metadata_mode = mode
        self._update_status_button_style()
        self.apply_filter()

    def open_duplicate_cleaner(self):
        dialog = MP3DuplicateCleaner(self)
        dialog.exec()
        self.load_data()

    def load_data(self):
        conn = get_connection()
        try:
            self.rows = conn.execute(
                """
                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,
                       m.genre,
                       EXISTS(
                           SELECT 1 FROM track_mp3 tm
                           WHERE tm.mp3_id = m.id
                       ) AS linked,
                       COALESCE((
                           SELECT r.artist || ' - ' || r.title ||
                                  ' / ' || t.position || ' ' || t.title
                           FROM track_mp3 tm
                           JOIN tracks t ON t.id = tm.track_id
                           JOIN releases r ON r.id = t.release_id
                           WHERE tm.mp3_id = m.id
                           ORDER BY tm.id
                           LIMIT 1
                       ), '') AS vinyl_link,
                       COALESCE(m.metadata_checked, 0) AS metadata_checked
                FROM mp3_files m
                ORDER BY
                    m.artist COLLATE NOCASE,
                    m.title COLLATE NOCASE,
                    m.path COLLATE NOCASE
                """
            ).fetchall()
        finally:
            conn.close()

        self.metadata_status_by_path = {
            str(row[0]): int(row[9] or 0)
            for row in self.rows
        }
        self.apply_filter()

    def apply_filter(self):
        query = self.search.text().strip().casefold()
        link_mode = self.filter.currentIndex()
        rows = []

        for row in self.rows:
            linked = int(row[7] or 0)
            checked = int(row[9] or 0)

            if link_mode == 1 and not linked:
                continue
            if link_mode == 2 and linked:
                continue

            if self.metadata_mode == "done" and not checked:
                continue
            if self.metadata_mode == "todo" and checked:
                continue

            hay = " ".join(
                str(value or "")
                for value in (
                    row[0], row[1], row[2], row[3], row[4], row[6], row[8]
                )
            ).casefold()

            if query and query not in hay:
                continue

            rows.append((
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[0],
                "VINYL" if linked else "LOS",
                "✓ KLAAR" if checked else "NIET GEDAAN",
                row[8],
                checked,
            ))

        self.filtered_rows = rows
        self.model.set_rows(rows)

        total = len(self.rows)
        done = sum(
            1 for row in self.rows
            if int(row[9] or 0) == 1
        )
        todo = total - done

        self.progress_label.setText(
            f"Metadata: {done} KLAAR | {todo} NIET GEDAAN | {total} TOTAAL"
        )
        self.info.setText(
            f"{len(rows)} zichtbaar | {done} KLAAR | {todo} NIET GEDAAN | totaal {total} MP3's"
        )

    def selected_row(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.rows[indexes[0].row()]

    def play_selected(self, *_args):
        row = self.selected_row()
        if row is None:
            return

        path = str(row[5] or "")
        if path and Path(path).exists():
            self.play_mp3.emit(path)
        else:
            QMessageBox.warning(
                self,
                "Bestand ontbreekt",
                path,
            )

    def open_selected_folder(self, *_args):
        import os
        import subprocess

        row = self.selected_row()
        if row is None:
            return

        path = Path(str(row[5] or ""))
        if not path.exists():
            QMessageBox.warning(
                self,
                "Bestand ontbreekt",
                str(path),
            )
            return

        try:
            subprocess.Popen(["explorer", "/select,", str(path)])
        except Exception:
            try:
                os.startfile(str(path.parent))
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Map openen mislukt",
                    str(exc),
                )

    def edit_selected_metadata(self, *_args):
        row = self.selected_row()
        if row is None:
            return

        if not MUTAGEN_AVAILABLE:
            QMessageBox.information(
                self,
                "Metadata Builder",
                "Installeer Mutagen met:\n\npython -m pip install mutagen",
            )
            return

        path = str(row[5] or "")
        if not Path(path).exists():
            QMessageBox.warning(
                self,
                "Bestand ontbreekt",
                path,
            )
            return

        dialog = MetadataDialog((path,), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

