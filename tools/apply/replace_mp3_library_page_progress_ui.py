from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")
start = text.find("class MP3LibraryPage(QWidget):")
if start < 0:
    raise RuntimeError("class MP3LibraryPage niet gevonden")

replacement = r'''class MP3LibraryPage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.filtered_rows = []
        self.metadata_status_by_path = {}
        self.metadata_mode = "all"
        ensure_mp3_metadata_progress()
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
'''

TARGET.write_text(text[:start] + replacement + "\n", encoding="utf-8-sig")
print("MP3 Library volledig vervangen: metadata voortgang + knoppen + gele status")
