from pathlib import Path

FILE = Path("gui/mp3_showcase_page.py")
text = FILE.read_text(encoding="utf-8-sig")

# Add table widgets to the existing imports.
old = "    QListWidget, QListWidgetItem, QFrame, QScrollArea, QSizePolicy,\n)"
new = "    QListWidget, QListWidgetItem, QFrame, QScrollArea, QSizePolicy,\n    QTableWidget, QTableWidgetItem, QHeaderView,\n)"
if old in text and "QTableWidget" not in text:
    text = text.replace(old, new, 1)

# Replace only the MP3 Showcase build_ui method. The vinyl deck itself is left untouched.
start = text.index("    def build_ui(self):", text.index("class MP3ShowcasePage"))
end = text.index("    def populate_list(self):", start)

new_build = '''    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        title = QLabel("MP3 SHOWCASE")
        title.setStyleSheet("font-size:26px;font-weight:900;color:#fff;")
        root.addWidget(title)

        search = QHBoxLayout()
        search.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand...")
        search.addWidget(self.search, 1)
        self.refresh = QPushButton("VERVERS")
        search.addWidget(self.refresh)
        root.addLayout(search)

        self.status = QLabel("0 MP3's")
        self.status.setStyleSheet("color:#9b9ba6;")
        root.addWidget(self.status)

        # Three stable horizontal zones:
        #   1. MP3 library table (artist + track)
        #   2. visual vinyl deck
        #   3. selected-track information / controls
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(14)

        left = QFrame()
        left.setObjectName("showcasePanel")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        left_title = QLabel("MP3 LIBRARY")
        left_title.setStyleSheet("color:#d84b91;font-size:12px;font-weight:900;letter-spacing:1px;")
        left_layout.addWidget(left_title)

        self.list = QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["ARTIEST", "TRACK"])
        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list.setAlternatingRowColors(True)
        self.list.setShowGrid(False)
        self.list.verticalHeader().setVisible(False)
        header = self.list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.list.currentCellChanged.connect(lambda row, *_: self.select_index(row))
        left_layout.addWidget(self.list, 1)
        body.addWidget(left, 5)

        center = QFrame()
        center.setObjectName("showcasePanel")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(8, 8, 8, 8)
        center_layout.setSpacing(8)
        self.vinyl_deck = VinylDeckWidget(self)
        center_layout.addWidget(self.vinyl_deck, 1)
        body.addWidget(center, 6)

        right = QFrame()
        right.setObjectName("showcasePanel")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        info_title = QLabel("CURRENT TRACK")
        info_title.setStyleSheet("color:#d84b91;font-size:12px;font-weight:900;letter-spacing:1px;")
        right_layout.addWidget(info_title)

        self.current_artist = QLabel("Onbekende artiest")
        self.current_artist.setWordWrap(True)
        self.current_artist.setStyleSheet("color:#d84b91;font-size:16px;font-weight:800;")
        right_layout.addWidget(self.current_artist)

        self.current_title = QLabel("Geen track geselecteerd")
        self.current_title.setWordWrap(True)
        self.current_title.setStyleSheet("color:#fff;font-size:22px;font-weight:900;")
        right_layout.addWidget(self.current_title)

        self.current_path = QLabel("")
        self.current_path.setWordWrap(True)
        self.current_path.setStyleSheet("color:#77717c;font-size:10px;")
        right_layout.addWidget(self.current_path)

        right_layout.addStretch(1)

        controls = QHBoxLayout()
        self.previous = QPushButton("VORIGE")
        self.play = QPushButton("PLAY")
        self.next = QPushButton("VOLGENDE")
        self.power = QPushButton("POWER")
        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        controls.addWidget(self.power)
        right_layout.addLayout(controls)
        body.addWidget(right, 3)

        root.addLayout(body, 1)

        self.previous.clicked.connect(self.previous_track)
        self.next.clicked.connect(self.next_track)
        self.play.clicked.connect(self.play_current)
        self.power.clicked.connect(lambda: self.vinyl_deck.set_power(not self.vinyl_deck.power_on))
        self.search.textChanged.connect(self.populate_list)
        self.refresh.clicked.connect(self.load_files)

        self.setStyleSheet("""
            QWidget{background:#0b0b0f;color:#f2f2f5;}
            QLineEdit,QPushButton{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;}
            QPushButton:hover{border-color:#d84b91;background:#24242c;}
            QFrame#showcasePanel{background:#101016;border:1px solid #292630;border-radius:10px;}
            QTableWidget{background:#0f0f14;color:#fff;border:1px solid #292630;border-radius:7px;alternate-background-color:#13131a;}
            QTableWidget::item{padding:8px;border-bottom:1px solid #24242d;}
            QTableWidget::item:selected{background:#3a1d31;color:#fff;}
            QHeaderView::section{background:#191820;color:#9d98a2;border:0;border-bottom:1px solid #38323d;padding:8px;font-weight:800;}
        """)

'''
text = text[:start] + new_build + text[end:]

# Replace populate_list so the table receives separate ARTIEST/TRACK columns.
start = text.index("    def populate_list(self):", text.index("class MP3ShowcasePage"))
end = text.index("    def select_index(self, index):", start)

new_populate = '''    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [
            row for row in self.items
            if not q or q in " ".join(str(x or "") for x in row).casefold()
        ]

        self.list.blockSignals(True)
        self.list.setRowCount(0)
        for row in self.visible_items:
            artist = str(row[1] or "").strip() or "Onbekende artiest"
            title = str(row[2] or "").strip() or Path(str(row[0])).stem
            r = self.list.rowCount()
            self.list.insertRow(r)
            artist_item = QTableWidgetItem(artist)
            title_item = QTableWidgetItem(title)
            artist_item.setToolTip(str(row[0]))
            title_item.setToolTip(str(row[0]))
            self.list.setItem(r, 0, artist_item)
            self.list.setItem(r, 1, title_item)
            self.list.setRowHeight(r, 42)
        self.list.blockSignals(False)

        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items:
            self.list.setCurrentCell(0, 0)
        else:
            self.current_index = -1
            self.clear_showcase()

'''
text = text[:start] + new_populate + text[end:]

# Update the selected-track display without touching playback/database logic.
old_show = '''        self.vinyl_deck.set_track(artist, title)\n        self.previous.setEnabled(self.current_index > 0)'''
new_show = '''        self.vinyl_deck.set_track(artist, title)\n        if hasattr(self, "current_artist"):\n            self.current_artist.setText(artist)\n            self.current_title.setText(title)\n            self.current_path.setText(str(row[0] or ""))\n        self.previous.setEnabled(self.current_index > 0)'''
text = text.replace(old_show, new_show, 1)

# Keep clear_showcase compatible with the new information panel.
old_clear = '''    def clear_showcase(self):\n        self.vinyl_deck.set_track("Onbekende artiest", "-")\n        self.vinyl_deck.set_playing(False)'''
new_clear = '''    def clear_showcase(self):\n        self.vinyl_deck.set_track("Onbekende artiest", "-")\n        self.vinyl_deck.set_playing(False)\n        if hasattr(self, "current_artist"):\n            self.current_artist.setText("Onbekende artiest")\n            self.current_title.setText("Geen track geselecteerd")\n            self.current_path.setText("")'''
text = text.replace(old_clear, new_clear, 1)

FILE.write_text(text, encoding="utf-8")
print("OK: MP3 Showcase is terug naar drie horizontale kolommen.")
print("ARTIEST | TRACK | VINYL DECK | CURRENT TRACK")
