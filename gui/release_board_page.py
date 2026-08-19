# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE BOARD
# ============================================================

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QFrame,
)

from database.database import get_connection
from gui.release_board_tile import ReleaseBoardTile


class ReleaseBoardPage(QWidget):

    open_release = __import__("PySide6.QtCore", fromlist=["Signal"]).Signal(int)
    play_mp3 = __import__("PySide6.QtCore", fromlist=["Signal"]).Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.all_releases = []
        self._last_columns = 0
        self._visible_rows = []
        self._render_index = 0
        self._page_size = 30

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.apply_search)

        self.build_ui()
        QTimer.singleShot(120, self.load_releases)

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title = QLabel("RELEASE BOARD")
        title.setObjectName("boardPageTitle")
        header.addWidget(title)

        subtitle = QLabel("Je collectie als cover-board — bekijken, openen en afspelen")
        subtitle.setObjectName("boardPageSubtitle")
        header.addWidget(subtitle)
        header.addStretch()

        self.count_label = QLabel("0 releases")
        self.count_label.setObjectName("boardCount")
        header.addWidget(self.count_label)

        layout.addLayout(header)

        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Zoek artiest, release, label, catalogus, jaar..."
        )
        self.search_input.setMinimumHeight(42)
        self.search_input.textChanged.connect(self.schedule_search)
        search_row.addWidget(self.search_input, 1)

        clear_button = QPushButton("WISSEN")
        clear_button.setMinimumHeight(42)
        clear_button.clicked.connect(self.search_input.clear)
        search_row.addWidget(clear_button)

        refresh_button = QPushButton("VERNIEUW")
        refresh_button.setMinimumHeight(42)
        refresh_button.clicked.connect(self.load_releases)
        search_row.addWidget(refresh_button)

        layout.addLayout(search_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(8, 8, 8, 18)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(18)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self.load_more_button = QPushButton("MEER RELEASES LADEN")
        self.load_more_button.setMinimumHeight(42)
        self.load_more_button.clicked.connect(self.load_more)
        self.load_more_button.setVisible(False)
        layout.addWidget(self.load_more_button)

        self.setStyleSheet(
            """
            QWidget {
                background: #0b0b0f;
                color: #f2f2f5;
                font-family: 'Segoe UI Semibold';
            }

            QLabel#boardPageTitle {
                background: transparent;
                color: #ffffff;
                font-size: 25px;
                font-weight: 800;
            }

            QLabel#boardPageSubtitle {
                background: transparent;
                color: #8d8d98;
                font-size: 13px;
                padding-left: 12px;
            }

            QLabel#boardCount {
                background: #15151b;
                color: #ff4fa3;
                border: 1px solid #3c2534;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 800;
            }

            QLineEdit {
                background: #15151b;
                color: #ffffff;
                border: 1px solid #2c2c35;
                border-radius: 7px;
                padding: 8px 12px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #ff4fa3;
            }

            QPushButton {
                background: #18181f;
                color: #ffffff;
                border: 1px solid #30303a;
                border-radius: 7px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 800;
            }

            QPushButton:hover {
                background: #23232c;
                border-color: #4c4c59;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QFrame#releaseBoardTile {
                background: #121217;
                border: 1px solid #292933;
                border-radius: 12px;
            }

            QFrame#releaseBoardTile:hover {
                background: #17171e;
                border-color: #575763;
            }

            QLabel#boardCover {
                background: #07070a;
                color: #666671;
                border: 1px solid #27272f;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 800;
            }

            QLabel#boardArtist {
                background: transparent;
                color: #ffcf72;
                font-size: 14px;
                font-weight: 800;
            }

            QLabel#boardTitle {
                background: transparent;
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#boardInfo {
                background: transparent;
                color: #8f8f9a;
                font-size: 10px;
            }

            QLabel#boardReady,
            QLabel#boardOpen {
                background: transparent;
                color: #ff4fa3;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#boardReady {
                color: #6fdd87;
            }

            QPushButton#boardOpenButton {
                background: #1c1c24;
            }

            QPushButton#boardPlayButton {
                background: #241422;
                color: #ff67ad;
                border-color: #4b263c;
            }

            QPushButton#boardPlayButton:hover {
                background: #ff4fa3;
                color: #0e0e12;
                border-color: #ff4fa3;
            }
            """
        )

    def load_releases(self):
        connection = None
        try:
            connection = get_connection()
            rows = connection.execute(
                """
                SELECT
                    r.id,
                    r.artist,
                    r.title,
                    r.label,
                    r.catalog,
                    r.year,
                    r.storage_code,
                    r.checked,
                    r.cover,
                    (
                        SELECT m.path
                        FROM track_mp3 tm
                        JOIN mp3_files m ON m.id = tm.mp3_id
                        JOIN tracks t ON t.id = tm.track_id
                        WHERE t.release_id = r.id
                          AND tm.is_preferred = 1
                        ORDER BY tm.id
                        LIMIT 1
                    ) AS preferred_mp3
                FROM releases r
                ORDER BY
                    r.artist COLLATE NOCASE,
                    r.title COLLATE NOCASE,
                    r.id
                """
            ).fetchall()
        finally:
            if connection is not None:
                connection.close()

        self.all_releases = [dict(row) if hasattr(row, "keys") else {
            "id": row[0], "artist": row[1], "title": row[2],
            "label": row[3], "catalog": row[4], "year": row[5],
            "checked": row[6], "cover": row[7], "preferred_mp3": row[8]
        } for row in rows]

        self.apply_search()

    def showEvent(self, event):
        super().showEvent(event)

        # Bij de eerste opening is de sidebar/layout soms nog niet volledig
        # uitgewerkt. Qt berekent dan tijdelijk een te kleine viewport, waardoor
        # de Board als een smal raster verschijnt. Na het tonen forceren we
        # alleen een nieuwe kolomberekening en herschikken we de reeds geladen
        # kaarten. Er worden geen nieuwe releases geladen.
        QTimer.singleShot(0, self.refresh_initial_layout)
        QTimer.singleShot(120, self.refresh_initial_layout)

    def refresh_initial_layout(self):
        if not hasattr(self, "scroll"):
            return

        columns = self.calculate_columns()
        if columns == self._last_columns:
            return

        self._last_columns = 0

        if hasattr(self, "_visible_rows"):
            rows = list(self._visible_rows)
        else:
            rows = self.filtered_rows() if hasattr(self, "all_releases") else []

        if rows:
            self.populate(rows)
        else:
            self.grid.invalidate()
            self.grid.activate()
            self.container.adjustSize()
            self.scroll.viewport().update()

    def schedule_search(self, _text=""):
        self.search_timer.start()

    def apply_search(self):
        text = self.search_input.text().strip().casefold()

        if not text:
            rows = self.all_releases
        else:
            rows = []
            for row in self.all_releases:
                haystack = " ".join([
                    str(row.get("artist") or ""),
                    str(row.get("title") or ""),
                    str(row.get("label") or ""),
                    str(row.get("catalog") or ""),
                    str(row.get("year") or ""),
                ]).casefold()
                if text in haystack:
                    rows.append(row)

        self.populate(rows)

    def clear_tiles(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def start_population(self, rows):
        self.clear_tiles()
        self._visible_rows = list(rows)
        self._render_index = 0
        self.count_label.setText(f"{len(self._visible_rows)} releases")
        self.load_more_button.setVisible(bool(self._visible_rows))
        self.load_more(initial=True)

    def load_more(self, initial=False):
        if not self._visible_rows:
            self.load_more_button.setVisible(False)
            return

        columns = max(1, self.calculate_columns())
        self._last_columns = columns

        end = min(
            self._render_index + self._page_size,
            len(self._visible_rows),
        )

        for index in range(self._render_index, end):
            row = self._visible_rows[index]
            tile = ReleaseBoardTile(row)
            tile.open_release.connect(self.open_release.emit)
            tile.play_mp3.connect(self.play_mp3.emit)
            self.grid.addWidget(tile, index // columns, index % columns)

        self._render_index = end
        self.load_more_button.setVisible(
            self._render_index < len(self._visible_rows)
        )

        if not initial and self._render_index >= len(self._visible_rows):
            self.load_more_button.setText("ALLES GELADEN")
        elif self._render_index < len(self._visible_rows):
            remaining = len(self._visible_rows) - self._render_index
            self.load_more_button.setText(
                f"MEER RELEASES LADEN  ({remaining} over)"
            )

    def populate(self, rows):
        self.start_population(rows)

    def calculate_columns(self):
        width = max(520, self.scroll.viewport().width() - 20)
        return max(1, width // 270)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = self.calculate_columns()
        if columns != self._last_columns and hasattr(self, "_visible_rows"):
            rows_to_keep = self._visible_rows[:self._render_index]
            if rows_to_keep:
                self.start_population(self._visible_rows)

    def filtered_rows(self):
        text = self.search_input.text().strip().casefold()
        if not text:
            return self.all_releases
        return [
            row for row in self.all_releases
            if text in " ".join([
                str(row.get("artist") or ""),
                str(row.get("title") or ""),
                str(row.get("label") or ""),
                str(row.get("catalog") or ""),
                str(row.get("year") or ""),
            ]).casefold()
        ]
