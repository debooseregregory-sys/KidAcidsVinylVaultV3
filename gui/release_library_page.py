# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE LIBRARY
# ============================================================

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QStyle,
)

from database.database import get_connection


# ============================================================
# CONSTANTS
# ============================================================

READY_BACKGROUND = QColor(
    255,
    235,
    150
)

READY_FOREGROUND = QColor(
    20,
    20,
    20
)

NORMAL_BACKGROUND = QColor(
    16,
    16,
    16
)

NORMAL_ALTERNATE_BACKGROUND = QColor(
    23,
    23,
    23
)


# ============================================================
# HELPERS
# ============================================================

def display_value(value):
    """
    Maakt lege databasewaarden zichtbaar.
    """

    if value is None:
        return "------------"

    text = str(value).strip()

    if not text:
        return "------------"

    return text


# ============================================================
# READY ITEM DELEGATE
# ============================================================

class ReleaseItemDelegate(QStyledItemDelegate):
    """
    Tekent KLAAR-releases rechtstreeks.
    """

    def paint(
        self,
        painter,
        option,
        index
    ):

        checked = index.data(
            Qt.ItemDataRole.UserRole
        )

        try:
            checked = int(
                checked or 0
            )
        except Exception:
            checked = 0

        # ----------------------------------------------------
        # Normale Qt-optie
        # ----------------------------------------------------

        opt = QStyleOptionViewItem(
            option
        )

        self.initStyleOption(
            opt,
            index
        )

        # ----------------------------------------------------
        # KLAAR
        # ----------------------------------------------------

        if checked == 1:

            painter.save()

            # Lichtgele volledige cel
            painter.fillRect(
                option.rect,
                QColor(
                    255,
                    235,
                    150
                )
            )

            # Tekstkleur
            opt.palette.setColor(
                QPalette.ColorRole.Text,
                QColor(
                    20,
                    20,
                    20
                )
            )

            opt.palette.setColor(
                QPalette.ColorRole.WindowText,
                QColor(
                    20,
                    20,
                    20
                )
            )

            # Achtergrond transparant maken zodat de
            # stylesheet het geel niet opnieuw overschrijft.
            opt.backgroundBrush = Qt.BrushStyle.NoBrush

            # Tekst tekenen
            style = opt.widget.style() if opt.widget else None

            if style is None:

                from PySide6.QtWidgets import QApplication

                style = QApplication.style()

            style.drawControl(
                QStyle.ControlElement.CE_ItemViewItem,
                opt,
                painter,
                opt.widget
            )

            painter.restore()

            return

        # ----------------------------------------------------
        # NORMALE RELEASE
        # ----------------------------------------------------

        super().paint(
            painter,
            option,
            index
        )


# ============================================================
# RELEASE LIBRARY PAGE
# ============================================================

class ReleaseLibraryPage(QWidget):

    release_selected = Signal(int, object)

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.all_releases = []

        self.status_filter = "all"

        self.build_ui()

        self.load_releases()

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(
        self
    ):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        layout.setSpacing(
            12
        )

        # ====================================================
        # TITLE
        # ====================================================

        title = QLabel(
            "VINYLVAULT RELEASE LIBRARY"
        )

        title.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            title
        )

        # ====================================================
        # SUBTITLE
        # ====================================================

        subtitle = QLabel(
            "Je volledige fysieke vinylcollectie"
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #888888;
                font-size: 14px;
            }
            """
        )

        layout.addWidget(
            subtitle
        )

        # ====================================================
        # SEARCH
        # ====================================================

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Zoek artiest, release, label, catalogus, "
            "storage, Discogs of genre..."
        )

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.textChanged.connect(
            self.filter_releases
        )

        search_layout.addWidget(
            self.search_input,
            1
        )

        # ----------------------------------------------------
        # REFRESH
        # ----------------------------------------------------

        self.refresh_button = QPushButton(
            "VERNIEUW"
        )

        self.refresh_button.setMinimumHeight(
            42
        )

        self.refresh_button.clicked.connect(
            self.load_releases
        )

        search_layout.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            search_layout
        )

        # ====================================================
        # STATUS
        # ====================================================

        self.status_label = QLabel(
            "Releases laden..."
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #aaaaaa;
                font-size: 13px;
            }
            """
        )

        layout.addWidget(
            self.status_label
        )

        # ====================================================
        # STATUS FILTER
        # ====================================================

        status_filter_layout = QHBoxLayout()

        self.all_button = QPushButton(
            "[ ALLES ]"
        )

        self.todo_button = QPushButton(
            "[ NOG TE DOEN ]"
        )

        self.checked_button = QPushButton(
            "[ ✓ KLAAR ]"
        )

        self.all_button.clicked.connect(
            lambda: self.set_status_filter("all")
        )

        self.todo_button.clicked.connect(
            lambda: self.set_status_filter("todo")
        )

        self.checked_button.clicked.connect(
            lambda: self.set_status_filter("checked")
        )

        status_filter_layout.addWidget(
            self.all_button
        )

        status_filter_layout.addWidget(
            self.todo_button
        )

        status_filter_layout.addWidget(
            self.checked_button
        )

        status_filter_layout.addStretch()

        layout.addLayout(
            status_filter_layout
        )

        # ====================================================
        # TABLE
        # ====================================================

        self.table = QTableWidget()

        self.table.setColumnCount(
            11
        )

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "ARTIST",
                "RELEASE",
                "LABEL",
                "CATALOG",
                "YEAR",
                "STORAGE",
                "TRACKS",
                "MP3",
                "DISCOGS",
                "GENRE",
            ]
        )

        # ----------------------------------------------------
        # Selection
        # ----------------------------------------------------

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # ----------------------------------------------------
        # Appearance
        # ----------------------------------------------------

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setShowGrid(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.setWordWrap(
            False
        )

        self.table.verticalHeader().setDefaultSectionSize(
            34
        )

        # ====================================================
        # READY DELEGATE
        # ====================================================

        self.table.setItemDelegate(
            ReleaseItemDelegate(
                self.table
            )
        )

        # ====================================================
        # HEADER
        # ====================================================

        header = self.table.horizontalHeader()

        header.setStretchLastSection(
            False
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            9,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            10,
            QHeaderView.ResizeMode.ResizeToContents
        )

        # ====================================================
        # DOUBLE CLICK
        # ====================================================

        self.table.cellDoubleClicked.connect(
            self.open_release
        )

        # ====================================================
        # STYLE
        # ====================================================

        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: #101010;
                alternate-background-color: #171717;
                color: #eeeeee;
                gridline-color: #292929;
                border: 1px solid #303030;
                selection-background-color: #383838;
                selection-color: #ffffff;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 6px;
                border: none;
            }

            QHeaderView::section {
                background-color: #202020;
                color: #ffffff;
                padding: 9px;
                border: none;
                border-right: 1px solid #303030;
                border-bottom: 1px solid #444444;
                font-weight: bold;
                font-size: 12px;
            }

            QLineEdit {
                background-color: #181818;
                color: #ffffff;
                border: 1px solid #383838;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #666666;
            }

            QPushButton {
                background-color: #222222;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #303030;
            }

            QPushButton:pressed {
                background-color: #181818;
            }
            """
        )

        layout.addWidget(
            self.table,
            1
        )

        # ====================================================
        # OPEN BUTTON
        # ====================================================

        self.open_button = QPushButton(
            "OPEN RELEASE"
        )

        self.open_button.setMinimumHeight(
            42
        )

        self.open_button.clicked.connect(
            self.open_selected_release
        )

        layout.addWidget(
            self.open_button
        )

    # ========================================================
    # LOAD RELEASES
    # ========================================================

    def load_releases(
        self
    ):

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
                    r.discogs,
                    r.genre,
                    r.checked,

                    COUNT(
                        DISTINCT t.id
                    ) AS tracks,

                    COUNT(
                        DISTINCT tm.mp3_id
                    ) AS mp3_count

                FROM releases r

                LEFT JOIN tracks t
                    ON t.release_id = r.id

                LEFT JOIN track_mp3 tm
                    ON tm.track_id = t.id

                GROUP BY
                    r.id

                ORDER BY
                    r.artist COLLATE NOCASE,
                    r.title COLLATE NOCASE,
                    r.id
                """
            ).fetchall()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Database fout",
                (
                    "De Release Library kon niet "
                    "worden geladen.\n\n"
                    f"{error}"
                )
            )

            return

        finally:

            if connection is not None:

                connection.close()

        self.all_releases = rows

        self.display_releases(
            rows
        )

    # ========================================================
    # DISPLAY RELEASES
    # ========================================================

    def display_releases(
        self,
        rows
    ):

        self.table.setSortingEnabled(
            False
        )

        self.table.setRowCount(
            0
        )

        for row_number, row in enumerate(
            rows
        ):

            self.table.insertRow(
                row_number
            )

            values = [
                display_value(
                    row["id"]
                ),
                display_value(
                    row["artist"]
                ),
                display_value(
                    row["title"]
                ),
                display_value(
                    row["label"]
                ),
                display_value(
                    row["catalog"]
                ),
                display_value(
                    row["year"]
                ),
                display_value(
                    row["storage_code"]
                ),
                display_value(
                    row["tracks"]
                ),
                display_value(
                    row["mp3_count"]
                ),
                display_value(
                    row["discogs"]
                ),
                display_value(
                    row["genre"]
                ),
            ]

            # ------------------------------------------------
            # CHECKED
            # ------------------------------------------------

            try:

                checked = int(
                    row["checked"] or 0
                )

            except Exception:

                checked = 0

            # ------------------------------------------------
            # ITEMS
            # ------------------------------------------------

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                # --------------------------------------------
                # Alignment
                # --------------------------------------------

                if column in (
                    0,
                    5,
                    7,
                    8,
                    9
                ):

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                else:

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft
                        | Qt.AlignmentFlag.AlignVCenter
                    )

                # --------------------------------------------
                # Tooltip
                # --------------------------------------------

                item.setToolTip(
                    str(value)
                )

                # --------------------------------------------
                # Checked status voor delegate
                # --------------------------------------------

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    checked
                )

                # --------------------------------------------
                # Opslaan
                # --------------------------------------------

                self.table.setItem(
                    row_number,
                    column,
                    item
                )

            # ------------------------------------------------
            # Hoogte
            # ------------------------------------------------

            self.table.setRowHeight(
                row_number,
                34
            )

        # ====================================================
        # SORTING TERUG AAN
        # ====================================================

        self.table.setSortingEnabled(
            True
        )

        # ====================================================
        # STATUS
        # ====================================================

        total = len(
            rows
        )

        checked_count = 0

        for row in rows:

            try:

                if int(
                    row["checked"] or 0
                ) == 1:

                    checked_count += 1

            except Exception:

                pass

        self.status_label.setText(
            f"{total} releases  |  "
            f"{checked_count} klaar"
        )

    # ========================================================
    # FILTER
    # ========================================================

    def set_status_filter(
        self,
        status
    ):

        self.status_filter = status

        self.filter_releases(
            self.search_input.text()
        )

    # ========================================================
    # FILTER RELEASES
    # ========================================================

    def filter_releases(
        self,
        text
    ):

        search = (
            text
            .strip()
            .lower()
        )

        filtered = []

        for row in self.all_releases:

            checked = False

            try:
                checked = int(
                    row["checked"] or 0
                ) == 1
            except Exception:
                checked = False

            # ------------------------------------------------
            # STATUS FILTER
            # ------------------------------------------------

            if self.status_filter == "todo" and checked:
                continue

            if self.status_filter == "checked" and not checked:
                continue

            # ------------------------------------------------
            # TEXT SEARCH
            # ------------------------------------------------

            if search:

                values = [
                    row["id"],
                    row["artist"],
                    row["title"],
                    row["label"],
                    row["catalog"],
                    row["year"],
                    row["storage_code"],
                    row["discogs"],
                    row["genre"],
                ]

                combined = " ".join(
                    "" if value is None
                    else str(value)
                    for value in values
                ).lower()

                if search not in combined:
                    continue

            filtered.append(
                row
            )

        self.display_releases(
            filtered
        )

    # ========================================================
    # OPEN DOUBLE CLICK
    # ========================================================

    def open_release(
        self,
        row,
        column
    ):

        item = self.table.item(
            row,
            0
        )

        if item is None:

            return

        try:

            release_id = int(
                item.text()
            )

        except Exception:

            return

        self.release_selected.emit(
            release_id,
            self.visible_release_ids()
        )

    # ========================================================
    # OPEN SELECTED
    # ========================================================

    def open_selected_release(
        self
    ):

        selected_rows = (
            self.table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:

            QMessageBox.information(
                self,
                "Geen release geselecteerd",
                "Selecteer eerst een release."
            )

            return

        row_number = (
            selected_rows[0].row()
        )

        item = self.table.item(
            row_number,
            0
        )

        if item is None:

            return

        try:

            release_id = int(
                item.text()
            )

        except Exception:

            QMessageBox.warning(
                self,
                "Ongeldige release",
                "De geselecteerde release heeft "
                "geen geldig ID."
            )

            return

        self.release_selected.emit(
            release_id,
            self.visible_release_ids()
        )

    # ========================================================
    # VISIBLE RELEASE IDS
    # ========================================================

    def visible_release_ids(self):

        release_ids = []

        for row in range(
            self.table.rowCount()
        ):

            item = self.table.item(
                row,
                0
            )

            if item is None:

                continue

            try:

                release_ids.append(
                    int(item.text())
                )

            except Exception:

                continue

        return release_ids

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(
        self
    ):

        self.load_releases()

    # ========================================================
    # SHOW ALL
    # ========================================================

    def show_all(
        self
    ):

        self.search_input.clear()

        self.display_releases(
            self.all_releases
        )


# ============================================================
# END
# ============================================================