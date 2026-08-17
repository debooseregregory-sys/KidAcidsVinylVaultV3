from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------
if "from gui.discogs_mp3_lookup import" not in text:
    marker = "from database.database import get_connection\n"
    insert = marker + "from gui.discogs_mp3_lookup import (\n    parse_filename,\n    search_releases,\n    get_release,\n    artist_names,\n    label_info,\n    genre_text,\n    release_format,\n)\n"
    if marker not in text:
        raise RuntimeError("Kan importblok niet vinden in mp3_library_page.py")
    text = text.replace(marker, insert, 1)

# ------------------------------------------------------------------
# Correct selected-path handling after the visible table columns were
# reordered to Artist / Title / Album / Year / BPM / Pad / Koppeling.
# ------------------------------------------------------------------
text = text.replace(
    "        path = str(row[0])\n        if not Path(path).exists():",
    "        path = str(row[5] or \"\")\n        if not Path(path).exists():",
    1,
)

# ------------------------------------------------------------------
# Replace the complete MetadataDialog with the Discogs-assisted version.
# ------------------------------------------------------------------
start = text.find("class MetadataDialog(QDialog):")
end = text.find("\n\nclass MP3LibraryPage(QWidget):", start)
if start < 0 or end < 0:
    raise RuntimeError("MetadataDialog block niet gevonden")

new_block = r'''class MetadataDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
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

        self.artist.setText(artist_names(self.release))
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

        artists = []
        for artist in track.get("artists") or []:
            if isinstance(artist, dict) and artist.get("name"):
                artists.append(str(artist["name"]).strip())
        if artists:
            self.artist.setText(", ".join(dict.fromkeys(artists)))

    def save(self):
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
                conn.commit()
            finally:
                conn.close()

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Metadata opslaan mislukt", str(exc))
'''

text = text[:start] + new_block + text[end:]

# The visible table row keeps the real path in column 5 (Pad). Do not use
# the Artist column as the file path when opening the editor.
old = '        path = str(row[0] or "")\n        if not Path(path).exists():'
new = '        path = str(row[5] or "")\n        if not Path(path).exists():'
text = text.replace(old, new, 1)

# Open the dialog with only the real path; MetadataDialog reads the actual tags.
old = '        dialog = MetadataDialog(dialog_row, self)'
if old in text:
    text = text.replace(old, '        dialog = MetadataDialog((path,), self)', 1)

TARGET.write_text(text, encoding="utf-8")
print("Discogs-assistent toegevoegd aan Metadata Builder.")
print("Bestandsnaam -> voorstel -> Discogs releases -> release -> track -> velden invullen.")
print("Geen automatische metadata-opslag zonder op OPSLAAN te drukken.")
