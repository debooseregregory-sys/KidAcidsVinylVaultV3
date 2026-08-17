from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

needle = '''        self.discogs_select_button = QPushButton(
            "[ RELEASE KIEZEN ]"
        )
        self.discogs_select_button.clicked.connect(
            self.select_discogs_release
        )
        lookup_row.addWidget(
            self.discogs_select_button
        )
        layout.addLayout(lookup_row)
'''

replacement = '''        self.discogs_select_button = QPushButton(
            "[ RELEASE KIEZEN ]"
        )
        self.discogs_select_button.clicked.connect(
            self.select_discogs_release
        )
        lookup_row.addWidget(
            self.discogs_select_button
        )
        layout.addLayout(lookup_row)

        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel("Discogs ID/link:"))
        self.manual_discogs = QLineEdit()
        self.manual_discogs.setPlaceholderText(
            "bv. 6882994 of https://www.discogs.com/release/6882994/..."
        )
        manual_row.addWidget(self.manual_discogs, 1)

        self.manual_discogs_button = QPushButton(
            "[ HANDMATIG OPHALEN ]"
        )
        self.manual_discogs_button.clicked.connect(
            self.fetch_manual_discogs_release
        )
        manual_row.addWidget(self.manual_discogs_button)
        layout.addLayout(manual_row)
'''

if needle not in text:
    raise RuntimeError("Discogs release-keuze blok niet gevonden")

text = text.replace(needle, replacement, 1)

needle_method = '''    def search_discogs(self):
'''
manual_method = '''    def fetch_manual_discogs_release(self):
        value = self.manual_discogs.text().strip()
        if not value:
            QMessageBox.information(
                self,
                "Discogs",
                "Geef een Discogs release-ID of volledige Discogs release-link in.",
            )
            return

        import re

        match = re.search(r"/release/(\\d+)", value)
        if match:
            release_id = match.group(1)
        else:
            match = re.fullmatch(r"\\d+", value)
            release_id = match.group(0) if match else ""

        if not release_id:
            QMessageBox.warning(
                self,
                "Discogs",
                "Geen geldig Discogs release-ID gevonden.",
            )
            return

        try:
            self.release = get_release(int(release_id))
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Discogs release ophalen mislukt",
                str(exc),
            )
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
            label = f"{position} | {title}" if position else title
            if duration:
                label += f" | {duration}"
            self.track_choice.addItem(label, index)
        self.track_choice.blockSignals(False)

        self.discogs_info.setText(
            f"Handmatige Discogs release {release_id} | "
            f"{self.release.get('title', '')} | "
            f"{self.release.get('year') or ''} | "
            f"{release_format(self.release)} | {label_info(self.release)}"
        )

        self._choose_best_track()
        self.apply_discogs_track()

'''
if needle_method not in text:
    raise RuntimeError("search_discogs methode niet gevonden")
text = text.replace(needle_method, manual_method + needle_method, 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("Handmatige Discogs release-ingang toegevoegd")
