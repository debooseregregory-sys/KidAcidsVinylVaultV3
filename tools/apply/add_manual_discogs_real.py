from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / 'gui' / 'mp3_library_page.py'
text = TARGET.read_text(encoding='utf-8-sig')

if 'self.manual_discogs_id' not in text:
    needle = '''        self.discogs_select_button = QPushButton(
            "[ RELEASE KIEZEN ]"
        )
        self.discogs_select_button.clicked.connect(
            self.select_discogs_release
        )
        lookup_row.addWidget(self.discogs_select_button)
        layout.addLayout(lookup_row)
'''
    replacement = needle + '''
        manual_row = QHBoxLayout()
        manual_row.addWidget(QLabel("Discogs ID/link:"))
        self.manual_discogs_id = QLineEdit()
        self.manual_discogs_id.setPlaceholderText("bijv. 6882994 of volledige Discogs release-URL")
        manual_row.addWidget(self.manual_discogs_id, 1)
        self.manual_discogs_button = QPushButton("[ HANDMATIG OPHALEN ]")
        self.manual_discogs_button.clicked.connect(self.fetch_manual_discogs_release)
        manual_row.addWidget(self.manual_discogs_button)
        layout.addLayout(manual_row)
'''
    if needle not in text:
        raise RuntimeError('Discogs lookup block niet gevonden')
    text = text.replace(needle, replacement, 1)

if 'def fetch_manual_discogs_release(self)' not in text:
    marker = '    def select_discogs_release(self):\n'
    method = '''    def fetch_manual_discogs_release(self):
        raw = self.manual_discogs_id.text().strip()
        if not raw:
            QMessageBox.information(self, "Discogs", "Geef een Discogs release-ID of volledige release-link in.")
            return

        import re
        match = re.search(r"(?:release/)?(\\d+)(?:[/?#].*)?$", raw)
        if not match:
            match = re.search(r"discogs\\.com/release/(\\d+)", raw, re.IGNORECASE)
        if not match:
            QMessageBox.warning(self, "Discogs", "Geen geldig Discogs release-ID gevonden.")
            return

        release_id = int(match.group(1))
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
        valid_tracks = []
        for index, track in enumerate(tracks):
            if not isinstance(track, dict):
                continue
            title = str(track.get("title") or "").strip()
            if not title:
                continue
            valid_tracks.append(track)
            position = str(track.get("position") or "").strip()
            duration = str(track.get("duration") or "").strip()
            label = f"{position} | {title}" if position else title
            if duration:
                label += f" | {duration}"
            self.track_choice.addItem(label, len(valid_tracks) - 1)
        self.track_choice.blockSignals(False)

        self.discogs_info.setText(
            f"Handmatig geladen: Discogs {release_id} | "
            f"{self.release.get('title', '')} | "
            f"{self.release.get('year') or ''} | "
            f"{release_format(self.release)} | {label_info(self.release)}"
        )
        self._choose_best_track()
        self.apply_discogs_track()

'''
    if marker not in text:
        raise RuntimeError('select_discogs_release niet gevonden')
    text = text.replace(marker, method + marker, 1)

TARGET.write_text(text, encoding='utf-8-sig')
print('Handmatige Discogs release lookup toegevoegd.')
