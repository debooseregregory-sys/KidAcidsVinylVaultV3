# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS RELEASE IMPORT PAGE
# ============================================================

import io
import sqlite3
from contextlib import redirect_stdout

import requests

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QSplitter,
)

import config

from import_release_v3 import (
    DB,
    get_release,
    import_release,
)


# ============================================================
# DISCOGS
# ============================================================

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}


# ============================================================
# SEARCH WORKER
# ============================================================

class DiscogsSearchWorker(QThread):

    results = Signal(list)
    failed = Signal(str)

    def __init__(self, query):
        super().__init__()

        self.query = query

    def run(self):

        try:

            response = requests.get(
                f"{API_URL}/database/search",
                params={
                    "q": self.query,
                    "type": "release",
                    "per_page": 50,
                    "page": 1,
                },
                headers=HEADERS,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            self.results.emit(
                data.get("results", [])
            )

        except Exception as exc:

            self.failed.emit(
                f"{type(exc).__name__}: {exc}"
            )


# ============================================================
# IMPORT WORKER
# ============================================================

class DiscogsImportWorker(QThread):

    output = Signal(str)

    finished_ok = Signal()

    failed = Signal(str)

    def __init__(self, release_id):

        super().__init__()

        self.release_id = release_id

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        conn = None

        try:

            conn = sqlite3.connect(DB)

            conn.row_factory = sqlite3.Row

            conn.execute(
                "PRAGMA foreign_keys = ON"
            )

            buffer = io.StringIO()

            with redirect_stdout(buffer):

                release = get_release(
                    self.release_id
                )

                import_release(
                    release,
                    conn
                )

            self.output.emit(
                buffer.getvalue()
            )

            self.finished_ok.emit()

        except Exception as exc:

            if conn:

                try:
                    conn.rollback()
                except Exception:
                    pass

            self.failed.emit(
                f"{type(exc).__name__}: {exc}"
            )

        finally:

            if conn:

                try:
                    conn.close()
                except Exception:
                    pass


# ============================================================
# PAGE
# ============================================================

class DiscogsImportPage(QWidget):

    import_finished = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.search_worker = None

        self.import_worker = None

        self.selected_release_id = None

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        layout.setSpacing(
            15
        )

        # ====================================================
        # TITLE
        # ====================================================

        title = QLabel(
            "Discogs Release Import"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
                background: transparent;
            }
            """
        )

        layout.addWidget(
            title
        )

        # ====================================================
        # DESCRIPTION
        # ====================================================

        description = QLabel(
            "Zoek rechtstreeks in Discogs en importeer "
            "een volledige release naar VinylVault."
        )

        description.setWordWrap(
            True
        )

        description.setStyleSheet(
            """
            QLabel {
                color: #cccccc;
                background: transparent;
                font-size: 14px;
            }
            """
        )

        layout.addWidget(
            description
        )

        # ====================================================
        # SEARCH
        # ====================================================

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Zoek bijvoorbeeld: Planetary Assault Systems"
        )

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #202020;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #777777;
            }
            """
        )

        self.search_input.returnPressed.connect(
            self.search_discogs
        )

        search_layout.addWidget(
            self.search_input
        )

        self.search_button = QPushButton(
            "[ ZOEK DISCOGS ]"
        )

        self.search_button.setMinimumHeight(
            42
        )

        self.search_button.setMinimumWidth(
            180
        )

        self.search_button.clicked.connect(
            self.search_discogs
        )

        search_layout.addWidget(
            self.search_button
        )

        layout.addLayout(
            search_layout
        )

        # ====================================================
        # RESULTS
        # ====================================================

        results_title = QLabel(
            "DISCOGS RESULTATEN"
        )

        results_title.setStyleSheet(
            """
            QLabel {
                color: #77cc77;
                font-size: 13px;
                font-weight: bold;
                padding-top: 5px;
            }
            """
        )

        layout.addWidget(
            results_title
        )

        self.results_list = QListWidget()

        self.results_list.setStyleSheet(
            """
            QListWidget {
                background-color: #171717;
                color: #dddddd;
                border: 1px solid #333333;
                border-radius: 6px;
                font-size: 13px;
            }

            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #292929;
            }

            QListWidget::item:selected {
                background-color: #303030;
                color: #ffffff;
            }

            QListWidget::item:hover {
                background-color: #252525;
            }
            """
        )

        self.results_list.itemDoubleClicked.connect(
            self.select_result
        )

        self.results_list.currentItemChanged.connect(
            self.result_selected
        )

        layout.addWidget(
            self.results_list,
            1
        )

        # ====================================================
        # IMPORT BUTTON
        # ====================================================

        button_layout = QHBoxLayout()

        self.import_button = QPushButton(
            "[ IMPORT SELECTIE ]"
        )

        self.import_button.setMinimumHeight(
            44
        )

        self.import_button.setMinimumWidth(
            220
        )

        self.import_button.setEnabled(
            False
        )

        self.import_button.setStyleSheet(
            """
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #333333;
            }

            QPushButton:disabled {
                background-color: #151515;
                color: #555555;
                border: 1px solid #292929;
            }
            """
        )

        self.import_button.clicked.connect(
            self.import_selected
        )

        button_layout.addWidget(
            self.import_button
        )

        self.status_label = QLabel(
            "Zoek een release in Discogs."
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #999999;
                font-size: 12px;
            }
            """
        )

        button_layout.addWidget(
            self.status_label,
            1
        )

        layout.addLayout(
            button_layout
        )

        # ====================================================
        # LOG
        # ====================================================

        log_title = QLabel(
            "IMPORT LOG"
        )

        log_title.setStyleSheet(
            """
            QLabel {
                color: #77cc77;
                font-size: 13px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            log_title
        )

        self.log = QPlainTextEdit()

        self.log.setReadOnly(
            True
        )

        self.log.setMinimumHeight(
            180
        )

        self.log.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #101010;
                color: #bbbbbb;
                border: 1px solid #333333;
                border-radius: 6px;
                font-family: Consolas;
                font-size: 11px;
            }
            """
        )

        layout.addWidget(
            self.log
        )

    # ========================================================
    # SEARCH DISCOGS
    # ========================================================

    def search_discogs(self):

        query = self.search_input.text().strip()

        if not query:

            QMessageBox.warning(
                self,
                "Zoeken",
                "Geef eerst een artiest of release in."
            )

            return

        self.search_button.setEnabled(
            False
        )

        self.import_button.setEnabled(
            False
        )

        self.selected_release_id = None

        self.results_list.clear()

        self.status_label.setText(
            "Discogs wordt doorzocht..."
        )

        self.search_worker = DiscogsSearchWorker(
            query
        )

        self.search_worker.results.connect(
            self.search_results_received
        )

        self.search_worker.failed.connect(
            self.search_failed
        )

        self.search_worker.finished.connect(
            self.search_worker_finished
        )

        self.search_worker.start()

    # ========================================================
    # SEARCH RESULTS
    # ========================================================

    def search_results_received(
        self,
        results
    ):

        self.results_list.clear()

        if not results:

            self.status_label.setText(
                "Geen releases gevonden."
            )

            return

        for result in results:

            release_id = result.get(
                "id"
            )

            title = result.get(
                "title",
                ""
            )

            year = result.get(
                "year",
                ""
            )

            label = result.get(
                "label",
                []
            )

            catno = result.get(
                "catno",
                ""
            )

            format_info = result.get(
                "format",
                []
            )

            label_text = ""

            if label:

                label_text = ", ".join(
                    str(x)
                    for x in label
                )

            format_text = ""

            if format_info:

                format_text = " | ".join(
                    str(x)
                    for x in format_info
                )

            text = (
                f"{title}"
                f"    |    "
                f"{year or '-'}"
                f"    |    "
                f"{label_text or '-'}"
                f"    |    "
                f"{catno or '-'}"
                f"    |    "
                f"{format_text or '-'}"
                f"    |    "
                f"ID {release_id}"
            )

            item = QListWidgetItem(
                text
            )

            item.setData(
                32,
                release_id
            )

            item.setToolTip(
                f"Discogs Release ID: {release_id}"
            )

            self.results_list.addItem(
                item
            )

        self.status_label.setText(
            f"{len(results)} releases gevonden."
        )

    # ========================================================
    # SEARCH FAILED
    # ========================================================

    def search_failed(
        self,
        error
    ):

        self.status_label.setText(
            "Discogs zoeken mislukt."
        )

        QMessageBox.critical(
            self,
            "Discogs fout",
            error
        )

    # ========================================================
    # SEARCH FINISHED
    # ========================================================

    def search_worker_finished(self):

        self.search_button.setEnabled(
            True
        )

    # ========================================================
    # RESULT SELECTED
    # ========================================================

    def result_selected(
        self,
        current,
        previous
    ):

        if not current:

            self.selected_release_id = None

            self.import_button.setEnabled(
                False
            )

            return

        release_id = current.data(
            32
        )

        self.selected_release_id = release_id

        self.import_button.setEnabled(
            True
        )

        self.status_label.setText(
            f"Release {release_id} geselecteerd."
        )

    # ========================================================
    # DOUBLE CLICK
    # ========================================================

    def select_result(
        self,
        item
    ):

        self.result_selected(
            item,
            None
        )

        self.import_selected()

    # ========================================================
    # IMPORT
    # ========================================================

    def import_selected(self):

        if not self.selected_release_id:

            return

        release_id = self.selected_release_id

        answer = QMessageBox.question(
            self,
            "Release importeren",
            (
                f"Discogs Release {release_id} importeren?\n\n"
                "De release en tracks worden aan VinylVault "
                "toegevoegd.\n\n"
                "Bestaande gegevens worden niet dubbel toegevoegd."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        self.import_button.setEnabled(
            False
        )

        self.search_button.setEnabled(
            False
        )

        self.results_list.setEnabled(
            False
        )

        self.log.clear()

        self.log.appendPlainText(
            "=" * 70
        )

        self.log.appendPlainText(
            f"IMPORT RELEASE {release_id}"
        )

        self.log.appendPlainText(
            "=" * 70
        )

        self.import_worker = DiscogsImportWorker(
            release_id
        )

        self.import_worker.output.connect(
            self.import_output
        )

        self.import_worker.finished_ok.connect(
            self.import_finished_ok
        )

        self.import_worker.failed.connect(
            self.import_failed
        )

        self.import_worker.start()

    # ========================================================
    # IMPORT OUTPUT
    # ========================================================

    def import_output(
        self,
        output
    ):

        self.log.appendPlainText(
            output
        )

    # ========================================================
    # IMPORT OK
    # ========================================================

    def import_finished_ok(self):

        self.results_list.setEnabled(
            True
        )

        self.search_button.setEnabled(
            True
        )

        self.import_button.setEnabled(
            True
        )

        self.status_label.setText(
            "Release succesvol geïmporteerd."
        )

        QMessageBox.information(
            self,
            "Import klaar",
            (
                "De Discogs release is succesvol "
                "aan VinylVault toegevoegd."
            )
        )

        self.import_finished.emit()

    # ========================================================
    # IMPORT FAILED
    # ========================================================

    def import_failed(
        self,
        error
    ):

        self.results_list.setEnabled(
            True
        )

        self.search_button.setEnabled(
            True
        )

        self.import_button.setEnabled(
            True
        )

        self.status_label.setText(
            "Import mislukt."
        )

        self.log.appendPlainText(
            ""
        )

        self.log.appendPlainText(
            "FOUT:"
        )

        self.log.appendPlainText(
            error
        )

        QMessageBox.critical(
            self,
            "Import fout",
            error
        )
