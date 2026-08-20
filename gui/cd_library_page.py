# ============================================================
# KID ACID'S VINYLVAULT V3
# CD LIBRARY
# ============================================================

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox,
)

from database.cd_database import get_cd_releases, ensure_cd_schema


class CDLibraryPage(QWidget):
    cd_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(160)
        self.search_timer.timeout.connect(self._apply_pending_search)
        self._pending_search = ""
        self.build_ui()
        self.load_releases()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 25, 25, 25)
        root.setSpacing(12)

        title = QLabel("VINYLVAULT CD LIBRARY")
        title.setStyleSheet("QLabel { color:#fff; font-size:28px; font-weight:bold; }")
        root.addWidget(title)

        subtitle = QLabel("Je volledige CD-collectie")
        subtitle.setStyleSheet("QLabel { color:#888; font-size:14px; }")
        root.addWidget(subtitle)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, type, label of catalogus...")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self._schedule_search)
        search_row.addWidget(self.search, 1)

        refresh = QPushButton("VERNIEUW")
        refresh.setMinimumHeight(42)
        refresh.clicked.connect(self.load_releases)
        search_row.addWidget(refresh)
        root.addLayout(search_row)

        self.status = QLabel("CD's laden...")
        self.status.setStyleSheet("QLabel { color:#aaa; font-size:13px; }")
        root.addWidget(self.status)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "ARTIST", "RELEASE", "TYPE", "LABEL", "CATALOG", "YEAR"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.cellDoubleClicked.connect(self._open_selected)
        self.table.setStyleSheet("""
            QTableWidget { background:#101010; alternate-background-color:#171717;
                color:#eee; gridline-color:#292929; border:1px solid #303030;
                selection-background-color:#383838; selection-color:#fff; font-size:13px; }
            QTableWidget::item { padding:6px; border:none; }
            QHeaderView::section { background:#202020; color:#fff; padding:9px;
                border:none; border-right:1px solid #303030; border-bottom:1px solid #444;
                font-weight:bold; font-size:12px; }
            QLineEdit { background:#181818; color:#fff; border:1px solid #383838;
                border-radius:4px; padding:8px 12px; font-size:14px; }
            QLineEdit:focus { border:1px solid #666; }
            QPushButton { background:#222; color:#fff; border:1px solid #3a3a3a;
                border-radius:4px; padding:8px 16px; font-weight:bold; }
            QPushButton:hover { background:#303030; }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.table, 1)

        open_button = QPushButton("OPEN CD")
        open_button.setMinimumHeight(42)
        open_button.clicked.connect(self.open_selected)
        root.addWidget(open_button)

    def load_releases(self):
        try:
            ensure_cd_schema()
            self.all_rows = get_cd_releases()
            self.display_releases(self.all_rows)
        except Exception as error:
            QMessageBox.critical(self, "Database fout", f"De CD Library kon niet worden geladen.\n\n{error}")

    def display_releases(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            values = [row["id"], row["artist"], row["title"], row["media_type"], row["label"], row["catalog"], row["year"] or ""]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value or "------------"))
                item.setToolTip(str(value or ""))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if c in (0, 3, 6)
                    else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(r, c, item)
            self.table.setRowHeight(r, 34)
        self.table.setSortingEnabled(True)
        self.status.setText(f"{len(rows)} CD's")

    def _schedule_search(self, text):
        self._pending_search = text
        self.search_timer.start()

    def _apply_pending_search(self):
        text = self._pending_search.strip().lower()
        if not text:
            self.display_releases(self.all_rows)
            return
        filtered = []
        for row in self.all_rows:
            values = [row[k] for k in ("id", "artist", "title", "media_type", "label", "catalog", "year")]
            if text in " ".join("" if v is None else str(v) for v in values).lower():
                filtered.append(row)
        self.display_releases(filtered)

    def _open_selected(self, row, column):
        self._emit_selected(row)

    def open_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Geen CD geselecteerd", "Selecteer eerst een CD.")
            return
        self._emit_selected(selected[0].row())

    def _emit_selected(self, row):
        item = self.table.item(row, 0)
        if item is not None:
            try:
                self.cd_selected.emit(int(item.text()))
            except ValueError:
                pass
