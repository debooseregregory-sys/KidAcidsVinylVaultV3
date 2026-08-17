from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old_import = "from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TRCK, TPOS, TCOM, TPE2, COMM"
new_import = "from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TBPM, TRCK, TPOS, TCOM, TPE2, COMM"
if old_import in text:
    text = text.replace(old_import, new_import, 1)

start = text.index("class MetadataDialog(QDialog):")
end = text.index("\n\nclass MP3LibraryPage(QWidget):", start)

new_block = r'''class MetadataDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.path = str(row[0] or "")
        self.setWindowTitle("MP3 Metadata Builder")
        self.resize(620, 430)

        tags = self.read_real_tags(self.path)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.artist = QLineEdit(tags["artist"])
        self.title = QLineEdit(tags["title"])
        self.album = QLineEdit(tags["album"])
        self.year = QLineEdit(tags["year"])
        self.bpm = QLineEdit(tags["bpm"])
        self.track = QLineEdit(tags["track"])
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

        self.status = QLabel(f"Bestand: {self.path}")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
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
            if comments:
                values = []
                for frame in comments:
                    try:
                        values.extend(str(value).strip() for value in frame.text if str(value).strip())
                    except Exception:
                        pass
                result["comment"] = " | ".join(dict.fromkeys(values))
        except Exception:
            pass

        return result

    def save(self):
        if not MUTAGEN_AVAILABLE:
            QMessageBox.warning(self, "Mutagen ontbreekt", "Installeer eerst Mutagen:\n\npython -m pip install mutagen")
            return

        path = self.path
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return

        try:
            try:
                tags = ID3(path)
            except ID3NoHeaderError:
                tags = ID3()

            def text(value):
                return str(value).strip()

            tags.delall("TPE1")
            if text(self.artist.text()):
                tags.add(TPE1(encoding=3, text=text(self.artist.text())))
            tags.delall("TIT2")
            if text(self.title.text()):
                tags.add(TIT2(encoding=3, text=text(self.title.text())))
            tags.delall("TALB")
            if text(self.album.text()):
                tags.add(TALB(encoding=3, text=text(self.album.text())))
            tags.delall("TCON")
            if text(self.genre.text()):
                tags.add(TCON(encoding=3, text=text(self.genre.text())))
            tags.delall("TDRC")
            if text(self.year.text()):
                tags.add(TDRC(encoding=3, text=text(self.year.text())))
            tags.delall("TBPM")
            if text(self.bpm.text()):
                tags.add(TBPM(encoding=3, text=text(self.bpm.text())))
            tags.delall("TRCK")
            if text(self.track.text()):
                tags.add(TRCK(encoding=3, text=text(self.track.text())))
            tags.delall("TPOS")
            if text(self.disc.text()):
                tags.add(TPOS(encoding=3, text=text(self.disc.text())))
            tags.delall("TPE2")
            if text(self.album_artist.text()):
                tags.add(TPE2(encoding=3, text=text(self.album_artist.text())))
            tags.delall("TCOM")
            if text(self.composer.text()):
                tags.add(TCOM(encoding=3, text=text(self.composer.text())))
            tags.delall("COMM")
            comment_text = text(self.comment.toPlainText())
            if comment_text:
                tags.add(COMM(encoding=3, lang="eng", desc="", text=comment_text))

            tags.save(path, v2_version=3)

            db_year = int(self.year.text()) if text(self.year.text()).isdigit() else None
            db_bpm = float(self.bpm.text()) if text(self.bpm.text()) else None

            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",
                    (text(self.artist.text()), text(self.title.text()), text(self.album.text()), db_year, text(self.genre.text()), db_bpm, path),
                )
                conn.commit()
            finally:
                conn.close()

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Metadata opslaan mislukt", str(exc))
'''

text = text[:start] + new_block + text[end:]

# edit_selected_metadata no longer needs to reconstruct metadata from database values.
old_method_start = text.index("    def edit_selected_metadata(")
# Keep the method through end-of-file and replace it.
new_method = r'''    def edit_selected_metadata(self, *_args):
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
        path = str(row[0] or "")
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return

        dialog = MetadataDialog((path,), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
'''
text = text[:old_method_start] + new_method + "\n"

TARGET.write_text(text, encoding="utf-8")
print("OK: Metadata Builder leest nu altijd de echte ID3-tags uit het MP3-bestand.")
