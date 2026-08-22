# ============================================================
# KID ACID'S MUSICVAULT V3
# MUSIC LIBRARY SETTINGS PANEL
# ============================================================

from pathlib import Path
import sqlite3

from PySide6.QtCore import QSettings, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from database.database import get_connection


class MusicLibrarySettingsPanel(QWidget):
    """Live Music Library controls without silently changing MP3 links."""

    action_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("Kid Acid", "MusicVault")
        self._stat_labels = {}
        self._path_label = None
        self._health_label = None
        self._review_window = None
        self._build_ui()
        self.refresh()

    def _music_folder(self):
        """Return the configured music folder, with the legacy path as fallback."""
        for key in ("music_folder", "mp3_folder", "mp3_root", "library_path"):
            value = self._settings.value(key, "")
            if value:
                return Path(str(value)).expanduser()
        return Path(r"D:\01. MP3’s")

    def _card(self):
        card = QFrame()
        card.setObjectName("musicLibraryCard")
        card.setStyleSheet("""
            QFrame#musicLibraryCard {
                background: #17171d;
                border: 1px solid #2d2d36;
                border-radius: 18px;
            }
            QLabel { color: #f4f4f7; }
            QPushButton {
                background: #24242d;
                color: #f5f5f7;
                border: 1px solid #3a3a45;
                border-radius: 10px;
                padding: 9px 16px;
                font-weight: 700;
            }
            QPushButton:hover { border-color: #d84b91; background: #2b2029; }
        """)
        return card

    def _stat(self, value, label, key):
        box = QFrame()
        box.setStyleSheet("QFrame { background:#111116; border-radius:14px; }")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(18, 16, 18, 16)
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size:24px;font-weight:900;color:#ffffff;")
        caption = QLabel(label.upper())
        caption.setStyleSheet("font-size:10px;font-weight:800;letter-spacing:1px;color:#8d8d98;")
        lay.addWidget(value_label)
        lay.addWidget(caption)
        self._stat_labels[key] = value_label
        return box

    def _section_title(self, title, subtitle):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:21px;font-weight:900;color:#ffffff;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size:12px;color:#90909b;")
        subtitle_label.setWordWrap(True)
        return title_label, subtitle_label

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(18)

        eyebrow = QLabel("MUSIC LIBRARY")
        eyebrow.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:2px;color:#d84b91;")
        root.addWidget(eyebrow)

        title, subtitle = self._section_title(
            "Your collection, at a glance",
            "Live information from your MusicVault database and configured MP3 source."
        )
        root.addWidget(title)
        root.addWidget(subtitle)

        overview = self._card()
        ol = QVBoxLayout(overview)
        ol.setContentsMargins(20, 20, 20, 20)
        ol.setSpacing(14)

        health_row = QHBoxLayout()
        self._health_label = QLabel("●  CHECKING LIBRARY")
        self._health_label.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:1px;color:#e6b84d;")
        health_row.addWidget(self._health_label)
        health_row.addStretch()
        source = QLabel("LIVE DATABASE")
        source.setStyleSheet("font-size:10px;font-weight:800;letter-spacing:1px;color:#777782;")
        health_row.addWidget(source)
        ol.addLayout(health_row)

        stats = QHBoxLayout()
        stats.setSpacing(10)
        stats.addWidget(self._stat("—", "MP3 FILES", "mp3"))
        stats.addWidget(self._stat("—", "TRACKS", "tracks"))
        stats.addWidget(self._stat("—", "LINKED TRACKS", "linked"))
        stats.addWidget(self._stat("—", "MISSING LINKS", "missing"))
        ol.addLayout(stats)
        root.addWidget(overview)

        folders = self._card()
        fl = QVBoxLayout(folders)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(12)
        ft, fs = self._section_title(
            "Music folder",
            "Choose the MP3 source used by MusicVault. The choice is stored locally and does not modify the database."
        )
        fl.addWidget(ft)
        fl.addWidget(fs)

        path_row = QHBoxLayout()
        self._path_label = QLabel()
        self._path_label.setStyleSheet(
            "background:#111116;border-radius:10px;padding:12px;color:#d5d5dc;"
            "font-family:Consolas;font-size:12px;"
        )
        self._path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._path_label.setTextInteractionFlags(self._path_label.textInteractionFlags())
        path_row.addWidget(self._path_label, 1)

        choose_btn = QPushButton("Choose Folder")
        choose_btn.clicked.connect(self._choose_folder)
        path_row.addWidget(choose_btn)

        open_btn = QPushButton("Open Folder")
        open_btn.clicked.connect(self._open_folder)
        path_row.addWidget(open_btn)
        fl.addLayout(path_row)
        root.addWidget(folders)

        workflow = self._card()
        wl = QVBoxLayout(workflow)
        wl.setContentsMargins(20, 20, 20, 20)
        wl.setSpacing(12)
        wt, ws = self._section_title(
            "Library workflow",
            "Jump directly to the existing MP3 tools. No automatic matching or deletion is performed from Settings."
        )
        wl.addWidget(wt)
        wl.addWidget(ws)

        buttons = QHBoxLayout()

        library_btn = QPushButton("Open MP3 Library")
        library_btn.clicked.connect(lambda: self._request_action("library"))
        buttons.addWidget(library_btn)

        scan_btn = QPushButton("Scan Library")
        scan_btn.clicked.connect(lambda: self._request_action("scan"))
        buttons.addWidget(scan_btn)

        missing_btn = QPushButton("Find Missing")
        missing_btn.clicked.connect(self._find_missing)
        buttons.addWidget(missing_btn)

        matches_btn = QPushButton("Review Matches")
        matches_btn.clicked.connect(lambda: self._request_action("matches"))
        buttons.addWidget(matches_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        buttons.addWidget(refresh_btn)

        wl.addLayout(buttons)
        root.addWidget(workflow)
        root.addStretch()

    def _main_window(self):
        """Return the real application window instead of relying on activeWindow()."""
        window = self.window()
        if window is not None and hasattr(window, "pages"):
            return window
        return None

    def _request_action(self, action):
        """Route Settings actions to the existing MusicVault window."""
        self.action_requested.emit(action)
        window = self._main_window()

        if action == "library":
            if window is not None and hasattr(window, "show_mp3_library"):
                window.show_mp3_library()
            return

        if action == "scan":
            if window is not None and hasattr(window, "show_mp3_library"):
                window.show_mp3_library()
                page = getattr(window, "mp3_library_page", None)
                if page is not None and hasattr(page, "load_data"):
                    page.load_data()
            QMessageBox.information(
                self,
                "Scan Library",
                "De MP3 Library is geopend en de actuele databasegegevens zijn opnieuw geladen.\n\n"
                "Deze actie wijzigt geen MP3-koppelingen en verwijdert geen bestanden."
            )
            return

        if action == "matches":
            self._open_match_reviewer(window)

    def _open_match_reviewer(self, window):
        """Open the existing full Discogs match reviewer and keep it alive."""
        try:
            try:
                import review_discogs_matches as reviewer_module
            except ModuleNotFoundError:
                from gui import review_discogs_matches as reviewer_module

            # The existing reviewer uses LOCAL_RESULTS in local_candidates(),
            # but that constant is missing from the legacy standalone module.
            # Supply the intended limit here without modifying the reviewer
            # logic or touching the database.
            if not hasattr(reviewer_module, "LOCAL_RESULTS"):
                reviewer_module.LOCAL_RESULTS = getattr(
                    reviewer_module,
                    "MAX_CANDIDATES",
                    12,
                )

            FullReviewWindow = reviewer_module.FullReviewWindow

            if self._review_window is not None:
                try:
                    self._review_window.raise_()
                    self._review_window.activateWindow()
                    return
                except RuntimeError:
                    self._review_window = None

            reviewer = FullReviewWindow()
            self._review_window = reviewer
            reviewer.setAttribute(reviewer.WidgetAttribute.WA_DeleteOnClose, True)
            reviewer.destroyed.connect(lambda: setattr(self, "_review_window", None))
            reviewer.show()
            reviewer.raise_()
            reviewer.activateWindow()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Review Matches",
                "De bestaande Match Reviewer kon niet worden geopend.\n\n"
                f"{type(exc).__name__}: {exc}"
            )

    def refresh(self):
        """Refresh path and database statistics without changing any records."""
        folder = self._music_folder()
        self._path_label.setText(str(folder))
        self._path_label.setToolTip(str(folder))

        try:
            connection = get_connection()
            try:
                mp3_count = connection.execute("SELECT COUNT(*) FROM mp3_files").fetchone()[0]
                track_count = connection.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
                linked_count = connection.execute(
                    "SELECT COUNT(DISTINCT track_id) FROM track_mp3"
                ).fetchone()[0]
                rows = connection.execute(
                    """
                    SELECT DISTINCT m.path
                    FROM track_mp3 x
                    INNER JOIN mp3_files m ON m.id = x.mp3_id
                    WHERE m.path IS NOT NULL AND TRIM(m.path) <> ''
                    """
                ).fetchall()
            finally:
                connection.close()

            missing_count = sum(1 for row in rows if not Path(str(row[0])).exists())

            self._stat_labels["mp3"].setText(f"{mp3_count:,}")
            self._stat_labels["tracks"].setText(f"{track_count:,}")
            self._stat_labels["linked"].setText(f"{linked_count:,}")
            self._stat_labels["missing"].setText(f"{missing_count:,}")

            if folder.exists() and folder.is_dir():
                self._health_label.setText("●  LIBRARY READY")
                self._health_label.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:1px;color:#72d69a;")
            else:
                self._health_label.setText("●  MUSIC FOLDER NOT FOUND")
                self._health_label.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:1px;color:#e6b84d;")
        except (sqlite3.Error, OSError) as exc:
            for key in self._stat_labels:
                self._stat_labels[key].setText("—")
            self._health_label.setText("●  DATABASE CHECK FAILED")
            self._health_label.setStyleSheet("font-size:11px;font-weight:900;letter-spacing:1px;color:#e35d6a;")
            self._health_label.setToolTip(str(exc))

    def _choose_folder(self):
        current = self._music_folder()
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Music Folder",
            str(current) if current.exists() else str(Path.home()),
        )
        if not selected:
            return

        self._settings.setValue("music_folder", selected)
        self.refresh()
        QMessageBox.information(
            self,
            "Music Folder",
            f"Music folder opgeslagen:\n\n{selected}\n\nDe database en bestaande MP3-koppelingen zijn niet gewijzigd."
        )

    def _open_folder(self):
        folder = self._music_folder()
        if folder.exists() and folder.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
            return
        QMessageBox.warning(self, "Music folder", f"De MP3-map bestaat niet:\n\n{folder}")

    def _find_missing(self):
        """Show a safe, read-only summary of broken MP3 paths."""
        try:
            connection = get_connection()
            try:
                rows = connection.execute(
                    """
                    SELECT DISTINCT m.path
                    FROM track_mp3 x
                    INNER JOIN mp3_files m ON m.id = x.mp3_id
                    WHERE m.path IS NOT NULL AND TRIM(m.path) <> ''
                    """
                ).fetchall()
            finally:
                connection.close()

            missing = [str(row[0]) for row in rows if not Path(str(row[0])).exists()]
            if not missing:
                QMessageBox.information(self, "Find Missing", "Er zijn geen ontbrekende MP3-paden gevonden.")
                return

            preview = "\n".join(missing[:25])
            if len(missing) > 25:
                preview += f"\n\n... en nog {len(missing) - 25}."
            QMessageBox.warning(
                self,
                "Find Missing",
                f"{len(missing):,} unieke MP3-paden bestaan niet meer.\n\n{preview}"
            )
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Find Missing", f"Databasecontrole mislukt:\n\n{exc}")
