# ============================================================
# KID ACID'S VINYLVAULT V3
# CD COLLECTION MODE
#
# Keeps the existing Vinyl UI and functionality intact while
# reusing the same Library, Board, Showcase, Detail, Discogs
# and MP3 flow for releases marked as CD.
# ============================================================

import io
import sqlite3
from contextlib import redirect_stdout

from PySide6.QtWidgets import QLabel, QMessageBox

from database.database import get_connection
from gui.release_library_page import ReleaseLibraryPage as BaseReleaseLibraryPage
from gui.release_board_page import ReleaseBoardPage as BaseReleaseBoardPage
from gui.discogs_import_page import (
    DiscogsImportPage as BaseDiscogsImportPage,
    DiscogsImportWorker as BaseDiscogsImportWorker,
    DB as DISCOGS_DB,
    get_release as discogs_get_release,
)
import gui.discogs_import_page as discogs_import_module
import gui.main_window as main_window_module


VINYL = "VINYL"
CD = "CD"


def normalize_media_type(value):
    value = str(value or VINYL).strip().upper()
    return CD if value == CD else VINYL


def ensure_media_type_column():
    """Safely add the media_type column to existing VinylVault databases."""
    conn = get_connection()
    try:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(releases)").fetchall()
        }

        if "media_type" not in columns:
            conn.execute(
                "ALTER TABLE releases ADD COLUMN media_type TEXT DEFAULT 'VINYL'"
            )

        conn.execute(
            """
            UPDATE releases
            SET media_type = 'VINYL'
            WHERE media_type IS NULL OR TRIM(media_type) = ''
            """
        )
        conn.commit()
    finally:
        conn.close()


class MediaReleaseLibraryPage(BaseReleaseLibraryPage):
    """Existing Release Library filtered by physical media type."""

    def __init__(self, parent=None, media_type=VINYL):
        self.media_type = normalize_media_type(media_type)
        super().__init__(parent)

        if self.media_type == CD:
            for label in self.findChildren(QLabel):
                if label.text() == "VINYLVAULT RELEASE LIBRARY":
                    label.setText("VINYLVAULT CD LIBRARY")
                elif label.text() == "Je volledige fysieke vinylcollectie":
                    label.setText("Je volledige fysieke CD-collectie")

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
                    r.discogs,
                    r.genre,
                    r.checked,
                    COALESCE(r.media_type, 'VINYL') AS media_type,
                    COUNT(DISTINCT t.id) AS tracks,
                    COUNT(DISTINCT tm.mp3_id) AS mp3_count
                FROM releases r
                LEFT JOIN tracks t ON t.release_id = r.id
                LEFT JOIN track_mp3 tm ON tm.track_id = t.id
                WHERE UPPER(COALESCE(r.media_type, 'VINYL')) = ?
                GROUP BY r.id
                ORDER BY r.artist COLLATE NOCASE,
                         r.title COLLATE NOCASE,
                         r.id
                """,
                (self.media_type,),
            ).fetchall()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Database fout",
                f"De {self.media_type} Library kon niet worden geladen.\n\n{error}",
            )
            return
        finally:
            if connection is not None:
                connection.close()

        self.all_releases = rows
        self.display_releases(rows)


class MediaReleaseBoardPage(BaseReleaseBoardPage):
    """Existing cover board filtered by physical media type."""

    def __init__(self, parent=None, media_type=VINYL):
        self.media_type = normalize_media_type(media_type)
        super().__init__(parent)

        if self.media_type == CD:
            for label in self.findChildren(QLabel):
                if label.text() == "RELEASE BOARD":
                    label.setText("CD RELEASE BOARD")
                elif label.text().startswith("Je collectie als cover-board"):
                    label.setText(
                        "Je CD-collectie als cover-board — bekijken, openen en afspelen"
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
                WHERE UPPER(COALESCE(r.media_type, 'VINYL')) = ?
                ORDER BY r.artist COLLATE NOCASE,
                         r.title COLLATE NOCASE,
                         r.id
                """,
                (self.media_type,),
            ).fetchall()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Database fout",
                f"De {self.media_type} Showcase kon niet worden geladen.\n\n{error}",
            )
            return
        finally:
            if connection is not None:
                connection.close()

        self.all_releases = [
            dict(row) if hasattr(row, "keys") else {
                "id": row[0], "artist": row[1], "title": row[2],
                "label": row[3], "catalog": row[4], "year": row[5],
                "storage_code": row[6], "checked": row[7],
                "cover": row[8], "preferred_mp3": row[9],
            }
            for row in rows
        ]
        self.apply_search()


class CDDiscogsImportWorker(BaseDiscogsImportWorker):
    """Same Discogs importer, but marks newly imported releases as CD."""

    def run(self):
        conn = None
        try:
            conn = sqlite3.connect(DISCOGS_DB)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")

            existing = conn.execute(
                "SELECT id, media_type FROM releases WHERE discogs = ? LIMIT 1",
                (str(self.release_id),),
            ).fetchone()

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                release = discogs_get_release(self.release_id)
                discogs_import_module.import_release(release, conn)

                if existing is None:
                    conn.execute(
                        "UPDATE releases SET media_type = 'CD' WHERE discogs = ?",
                        (str(self.release_id),),
                    )
                    conn.commit()
                    print("Media type: CD")
                else:
                    print(
                        "Bestaande release behouden als "
                        f"{existing['media_type'] or VINYL}."
                    )

            self.output.emit(buffer.getvalue())
            self.finished_ok.emit()

        except Exception as exc:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


class CDDiscogsImportPage(BaseDiscogsImportPage):
    """The existing Discogs page running in CD mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        for label in self.findChildren(QLabel):
            if label.text() == "Discogs Release Import":
                label.setText("Discogs CD Import")
            elif (
                "importeer" in label.text().lower()
                and "volledige release" in label.text().lower()
            ):
                label.setText(
                    "Zoek rechtstreeks in Discogs en importeer een volledige CD-release naar VinylVault."
                )

    def import_selected(self):
        old_worker = discogs_import_module.DiscogsImportWorker
        discogs_import_module.DiscogsImportWorker = CDDiscogsImportWorker
        try:
            super().import_selected()
        finally:
            discogs_import_module.DiscogsImportWorker = old_worker


OriginalVinylVaultWindow = main_window_module.VinylVaultWindow


class CDVinylVaultWindow(OriginalVinylVaultWindow):
    """Original main window plus the CD collection routes."""

    def build_ui(self):
        super().build_ui()

        self.current_media_type = VINYL

        # The original Detail/Showcase pages are shared by Vinyl and CD.
        self.detail_page.back_requested.connect(self._detail_back)
        self.showcase_page.back_requested.connect(self._showcase_back)
        self.showcase_page.edit_requested.connect(self._showcase_edit)

        # Reuse the exact same Library/Board/Showcase/Detail stack.
        self.cd_library_page = MediaReleaseLibraryPage(media_type=CD)
        self.cd_library_page.release_selected.connect(self._open_cd_release)
        self.pages.addWidget(self.cd_library_page)

        self.cd_board_page = MediaReleaseBoardPage(media_type=CD)
        self.cd_board_page.open_release.connect(self._show_cd_showcase)
        self.cd_board_page.play_mp3.connect(self.player_bar_play)
        self.pages.addWidget(self.cd_board_page)

        # Same Discogs UI, same search, same importer, CD media flag.
        self.cd_discogs_page = CDDiscogsImportPage()
        self.cd_discogs_page.import_finished.connect(self.refresh_after_import)
        self.pages.addWidget(self.cd_discogs_page)

        # Activate the CD navigation buttons.
        self.cd_showcase_button.setEnabled(True)
        self.cd_showcase_button.setToolTip("CD Showcase")
        self.cd_showcase_button.clicked.connect(self.show_cd_showcase_board)

        self.cd_library_button.setEnabled(True)
        self.cd_library_button.setToolTip("CD Library")
        self.cd_library_button.clicked.connect(self.show_cd_library)

        footer = self.findChild(QLabel, "sidebarFooter")
        if footer is not None:
            footer.setText("VINYL  •  CD  •  KID ACID")

        self._set_collection_badge(VINYL)

    def _set_collection_badge(self, media_type):
        badge = self.findChild(QLabel, "collectionBadge")
        if badge is not None:
            badge.setText(f"{normalize_media_type(media_type)} COLLECTION")

    def set_active_nav(self, button):
        super().set_active_nav(button)

        buttons = [
            self.cd_showcase_button,
            self.cd_library_button,
        ]
        for item in buttons:
            item.setProperty("active", item is button)
            item.style().unpolish(item)
            item.style().polish(item)

        self.current_nav = button

    def show_board(self):
        """Handle the shared board callback without assuming board_button exists."""
        if self.current_media_type == CD:
            self.show_cd_showcase_board()
            return

        self.pages.setCurrentWidget(self.board_page)
        self.page_title.setText("Release Board")

        # Some older VinylVault layouts had a board_button; the current
        # layout does not. Use the Vinyl Showcase navigation as the safe
        # active navigation target when the board is reached internally.
        if hasattr(self, "board_button"):
            self.set_active_nav(self.board_button)
        else:
            self.set_active_nav(self.vinyl_showcase_button)

    def show_vinyl_showcase(self):
        self.current_media_type = VINYL
        self._set_collection_badge(VINYL)
        super().show_vinyl_showcase()

    def show_library(self):
        self.current_media_type = VINYL
        self._set_collection_badge(VINYL)
        super().show_library()

    def open_release(self, release_id, release_ids=None):
        self.current_media_type = VINYL
        self._set_collection_badge(VINYL)
        super().open_release(release_id, release_ids)

    def show_showcase(self, release_id):
        self.current_media_type = VINYL
        self._set_collection_badge(VINYL)
        super().show_showcase(release_id)

    def show_cd_showcase_board(self):
        self.current_media_type = CD
        self._set_collection_badge(CD)
        self.pages.setCurrentWidget(self.cd_board_page)
        self.page_title.setText("CD Showcase")
        self.set_active_nav(self.cd_showcase_button)
        self.cd_board_page.load_releases()

    def show_cd_library(self):
        self.current_media_type = CD
        self._set_collection_badge(CD)
        self.pages.setCurrentWidget(self.cd_library_page)
        self.page_title.setText("CD Library")
        self.set_active_nav(self.cd_library_button)
        self.cd_library_page.load_releases()

    def _open_cd_release(self, release_id, release_ids=None):
        self.current_media_type = CD
        self._set_collection_badge(CD)
        self.showcase_page.load_release(release_id)
        self.pages.setCurrentWidget(self.showcase_page)
        self.page_title.setText("CD Showcase")
        self.set_active_nav(self.cd_showcase_button)

    def _show_cd_showcase(self, release_id):
        self._open_cd_release(release_id)

    def _detail_back(self):
        if self.current_media_type == CD:
            self.show_cd_library()
        else:
            self.show_library()

    def _showcase_back(self):
        if self.current_media_type == CD:
            self.show_cd_showcase_board()
        else:
            self.show_vinyl_showcase()

    def _showcase_edit(self, release_id):
        self.detail_page.load_release(release_id)
        self.pages.setCurrentWidget(self.detail_page)
        self.page_title.setText(
            "CD Detail" if self.current_media_type == CD else "Release Detail"
        )
        self._set_collection_badge(self.current_media_type)

    def show_discogs(self):
        if self.current_media_type == CD:
            self.pages.setCurrentWidget(self.cd_discogs_page)
            self.page_title.setText("Discogs CD Import")
            self.set_active_nav(self.discogs_button)
        else:
            super().show_discogs()

    def refresh_after_import(self):
        super().refresh_after_import()
        self.cd_library_page.load_releases()
        self.cd_board_page.load_releases()


def install_cd_mode():
    """Install the CD-enabled window before run_v3 calls main()."""
    ensure_media_type_column()
    main_window_module.VinylVaultWindow = CDVinylVaultWindow
