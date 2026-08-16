import os
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

DB = os.path.join(
    ROOT,
    "data",
    "vinylvault.db"
)


class VinylVaultV3(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Kid Acid's Vinyl Vault V3"
        )

        self.resize(
            1550,
            900
        )

        self.build_ui()

        self.search_releases()


    # ======================================================
    # DATABASE
    # ======================================================

    def database(self):

        return sqlite3.connect(
            DB
        )


    # ======================================================
    # UI
    # ======================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main = QVBoxLayout(
            central
        )

        main.setContentsMargins(
            20,
            20,
            20,
            20
        )

        main.setSpacing(
            12
        )

        # ==================================================
        # HEADER
        # ==================================================

        header = QHBoxLayout()

        title = QLabel(
            "KID ACID'S VINYL VAULT"
        )

        title.setFont(
            QFont(
                "Arial",
                26,
                QFont.Bold
            )
        )

        header.addWidget(
            title
        )

        header.addStretch()

        self.status = QLabel(
            "Klaar"
        )

        header.addWidget(
            self.status
        )

        main.addLayout(
            header
        )

        # ==================================================
        # SEARCH
        # ==================================================

        search = QHBoxLayout()

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Zoek artiest, track, release of kastcode..."
        )

        self.search.setMinimumHeight(
            44
        )

        self.search.setFont(
            QFont(
                "Arial",
                13
            )
        )

        self.search.textChanged.connect(
            self.search_releases
        )

        search.addWidget(
            self.search
        )

        clear = QPushButton(
            "WISSEN"
        )

        clear.setMinimumHeight(
            44
        )

        clear.clicked.connect(
            self.search.clear
        )

        search.addWidget(
            clear
        )

        refresh = QPushButton(
            "↻ VERVERS"
        )

        refresh.setMinimumHeight(
            44
        )

        refresh.clicked.connect(
            self.search_releases
        )

        search.addWidget(
            refresh
        )

        main.addLayout(
            search
        )

        # ==================================================
        # MAIN SPLITTER
        # ==================================================

        splitter = QSplitter(
            Qt.Horizontal
        )

        main.addWidget(
            splitter
        )

        # ==================================================
        # LEFT - RELEASES
        # ==================================================

        left = QFrame()

        left_layout = QVBoxLayout(
            left
        )

        left_title = QLabel(
            "COLLECTIE"
        )

        left_title.setFont(
            QFont(
                "Arial",
                16,
                QFont.Bold
            )
        )

        left_layout.addWidget(
            left_title
        )

        self.release_list = QListWidget()

        self.release_list.itemClicked.connect(
            self.release_selected
        )

        left_layout.addWidget(
            self.release_list
        )

        splitter.addWidget(
            left
        )

        # ==================================================
        # RIGHT - RELEASE DETAIL
        # ==================================================

        right = QFrame()

        right_layout = QVBoxLayout(
            right
        )

        # --------------------------------------------------
        # ARTIST
        # --------------------------------------------------

        self.artist_label = QLabel(
            "Selecteer een release"
        )

        self.artist_label.setFont(
            QFont(
                "Arial",
                28,
                QFont.Bold
            )
        )

        right_layout.addWidget(
            self.artist_label
        )

        # --------------------------------------------------
        # RELEASE
        # --------------------------------------------------

        self.release_label = QLabel(
            ""
        )

        self.release_label.setFont(
            QFont(
                "Arial",
                23
            )
        )

        right_layout.addWidget(
            self.release_label
        )

        # --------------------------------------------------
        # INFO
        # --------------------------------------------------

        self.info_label = QLabel(
            ""
        )

        self.info_label.setFont(
            QFont(
                "Arial",
                14
            )
        )

        self.info_label.setWordWrap(
            True
        )

        right_layout.addWidget(
            self.info_label
        )

        # --------------------------------------------------
        # SEPARATOR
        # --------------------------------------------------

        line = QFrame()

        line.setFrameShape(
            QFrame.HLine
        )

        right_layout.addWidget(
            line
        )

        # --------------------------------------------------
        # TRACKLIST TITLE
        # --------------------------------------------------

        tracks_title = QLabel(
            "TRACKLIST"
        )

        tracks_title.setFont(
            QFont(
                "Arial",
                17,
                QFont.Bold
            )
        )

        right_layout.addWidget(
            tracks_title
        )

        # --------------------------------------------------
        # TRACKLIST
        # --------------------------------------------------

        self.tracks = QTableWidget()

        self.tracks.setColumnCount(
            4
        )

        self.tracks.setHorizontalHeaderLabels([
            "POSITIE",
            "ARTIST",
            "TRACK",
            "DUUR"
        ])

        self.tracks.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        self.tracks.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        self.tracks.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        self.tracks.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        self.tracks.setAlternatingRowColors(
            True
        )

        self.tracks.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.tracks.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.tracks.setMinimumHeight(
            350
        )

        right_layout.addWidget(
            self.tracks
        )

        # --------------------------------------------------
        # BUTTONS
        # --------------------------------------------------

        buttons = QHBoxLayout()

        self.play_button = QPushButton(
            "▶  PLAY TRACK"
        )

        self.play_button.setMinimumHeight(
            46
        )

        buttons.addWidget(
            self.play_button
        )

        self.discogs_button = QPushButton(
            "🔗 DISCOGS"
        )

        self.discogs_button.setMinimumHeight(
            46
        )

        buttons.addWidget(
            self.discogs_button
        )

        buttons.addStretch()

        right_layout.addLayout(
            buttons
        )

        splitter.addWidget(
            right
        )

        splitter.setSizes([
            430,
            1050
        ])

        # ==================================================
        # FOOTER
        # ==================================================

        self.footer = QLabel(
            "VinylVault V3"
        )

        main.addWidget(
            self.footer
        )


    # ======================================================
    # SEARCH
    # ======================================================

    def search_releases(self):

        text = self.search.text().strip()

        self.release_list.clear()

        if not os.path.exists(DB):

            self.status.setText(
                "DATABASE NIET GEVONDEN"
            )

            return

        conn = self.database()

        cur = conn.cursor()

        if text:

            like = f"%{text}%"

            rows = cur.execute("""
                SELECT
                    r.id,
                    r.artist,
                    r.title,
                    r.discogs,
                    r.storage_code,
                    COUNT(t.id)

                FROM releases r

                LEFT JOIN tracks t
                    ON t.release_id = r.id

                WHERE
                    r.artist LIKE ?
                    OR r.title LIKE ?
                    OR r.storage_code LIKE ?
                    OR t.title LIKE ?

                GROUP BY r.id

                ORDER BY
                    r.artist COLLATE NOCASE,
                    r.title COLLATE NOCASE

                LIMIT 500
            """, (
                like,
                like,
                like,
                like
            )).fetchall()

        else:

            rows = cur.execute("""
                SELECT
                    r.id,
                    r.artist,
                    r.title,
                    r.discogs,
                    r.storage_code,
                    COUNT(t.id)

                FROM releases r

                LEFT JOIN tracks t
                    ON t.release_id = r.id

                GROUP BY r.id

                ORDER BY
                    r.artist COLLATE NOCASE,
                    r.title COLLATE NOCASE

                LIMIT 500
            """).fetchall()

        conn.close()

        for row in rows:

            release_id = row[0]

            artist = (
                row[1]
                or "Onbekend"
            )

            title = (
                row[2]
                or "(geen titel)"
            )

            storage = (
                row[4]
                or ""
            )

            track_count = row[5]

            if storage:

                text_value = (
                    f"{artist} — {title}"
                    f"   [{storage}]"
                )

            else:

                text_value = (
                    f"{artist} — {title}"
                )

            item = QListWidgetItem(
                text_value
            )

            item.setData(
                Qt.UserRole,
                release_id
            )

            item.setToolTip(
                f"Tracks: {track_count}\n"
                f"Kastcode: {storage or '-'}\n"
                f"Discogs: {row[3] or '-'}"
            )

            self.release_list.addItem(
                item
            )

        self.status.setText(
            f"{len(rows)} releases gevonden"
        )


    # ======================================================
    # RELEASE SELECT
    # ======================================================

    def release_selected(
        self,
        item
    ):

        release_id = item.data(
            Qt.UserRole
        )

        self.load_release(
            release_id
        )


    # ======================================================
    # LOAD RELEASE
    # ======================================================

    def load_release(
        self,
        release_id
    ):

        conn = self.database()

        cur = conn.cursor()

        release = cur.execute("""
            SELECT
                id,
                artist,
                title,
                discogs,
                year,
                storage_code
            FROM releases
            WHERE id = ?
        """, (
            release_id,
        )).fetchone()

        if not release:

            conn.close()

            return

        artist = (
            release[1]
            or "Onbekend"
        )

        title = (
            release[2]
            or "(geen titel)"
        )

        discogs = (
            release[3]
            or "-"
        )

        year = (
            release[4]
            or "-"
        )

        storage = (
            release[5]
            or "-"
        )

        self.artist_label.setText(
            artist
        )

        self.release_label.setText(
            title
        )

        self.info_label.setText(
            f"<b>KASTCODE:</b> {storage}"
            f"     |     "
            f"<b>JAAR:</b> {year}"
            f"     |     "
            f"<b>DISCOGS:</b> {discogs}"
        )

        tracks = cur.execute("""
            SELECT
                position,
                artist,
                title,
                duration
            FROM tracks
            WHERE release_id = ?
            ORDER BY id
        """, (
            release_id,
        )).fetchall()

        conn.close()

        self.tracks.setRowCount(
            len(tracks)
        )

        self.tracks.clearContents()

        for row_number, track in enumerate(
            tracks
        ):

            position = (
                track[0]
                or ""
            )

            track_artist = (
                track[1]
                or ""
            )

            track_title = (
                track[2]
                or ""
            )

            duration = track[3]

            if (
                isinstance(
                    duration,
                    (int, float)
                )
                and duration > 0
            ):

                minutes = int(
                    duration // 60
                )

                seconds = int(
                    duration % 60
                )

                duration_text = (
                    f"{minutes}:{seconds:02d}"
                )

            else:

                duration_text = ""

            values = [
                position,
                track_artist,
                track_title,
                duration_text
            ]

            for column, value in enumerate(
                values
            ):

                cell = QTableWidgetItem(
                    value
                )

                if column == 0:

                    cell.setTextAlignment(
                        Qt.AlignCenter
                    )

                self.tracks.setItem(
                    row_number,
                    column,
                    cell
                )

        self.footer.setText(
            f"{len(tracks)} tracks — "
            f"{artist} — {title}"
        )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    app = QApplication([])

    window = VinylVaultV3()

    window.show()

    app.exec()
