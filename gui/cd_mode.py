# ============================================================
# KID ACID'S VINYLVAULT V3
# CD COLLECTION MODE
# ============================================================

from database.database import get_connection
import gui.main_window as main_window_module
from gui.cd_library_page import CDLibraryPage
from gui.cd_board_page import CDBoardPage
from gui.cd_discogs_import_page import CDDiscogsImportPage

VINYL = "VINYL"
CD = "CD"


def normalize_media_type(value):
    return CD if str(value or VINYL).strip().upper() == CD else VINYL


def ensure_media_type_column():
    """Keep the existing Vinyl schema compatible with the CD mode."""
    conn = get_connection()
    try:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(releases)").fetchall()}
        if "media_type" not in columns:
            conn.execute("ALTER TABLE releases ADD COLUMN media_type TEXT DEFAULT 'VINYL'")
        conn.execute("UPDATE releases SET media_type='VINYL' WHERE media_type IS NULL OR TRIM(media_type)=''")
        conn.commit()
    finally:
        conn.close()


OriginalVinylVaultWindow = main_window_module.VinylVaultWindow


class CDVinylVaultWindow(OriginalVinylVaultWindow):
    """Existing VinylVault window extended with the dedicated CD pages."""

    def build_ui(self):
        super().build_ui()
        self.current_media_type = VINYL

        self.cd_library_page = CDLibraryPage()
        self.cd_board_page = CDBoardPage()
        self.cd_discogs_page = CDDiscogsImportPage()

        self.pages.addWidget(self.cd_library_page)
        self.pages.addWidget(self.cd_board_page)
        self.pages.addWidget(self.cd_discogs_page)

        self.cd_library_page.release_selected.connect(self._open_cd_release)
        self.cd_board_page.open_release.connect(self._show_cd_showcase)
        self.cd_board_page.play_mp3.connect(self.player_bar_play)
        self.cd_discogs_page.import_finished.connect(self.refresh_after_import)

        self.cd_showcase_button.setEnabled(True)
        self.cd_showcase_button.setToolTip("CD Showcase")
        self.cd_showcase_button.clicked.connect(self.show_cd_showcase_board)

        self.cd_library_button.setEnabled(True)
        self.cd_library_button.setToolTip("CD Library")
        self.cd_library_button.clicked.connect(self.show_cd_library)

        self._set_collection_badge(VINYL)

    def _set_collection_badge(self, media_type):
        from PySide6.QtWidgets import QLabel
        badge = self.findChild(QLabel, "collectionBadge")
        if badge:
            badge.setText(f"{normalize_media_type(media_type)} COLLECTION")

    def set_active_nav(self, button):
        super().set_active_nav(button)
        for item in (self.cd_showcase_button, self.cd_library_button):
            item.setProperty("active", item is button)
            item.style().unpolish(item)
            item.style().polish(item)

    def show_board(self):
        if self.current_media_type == CD:
            self.show_cd_showcase_board()
            return
        self.pages.setCurrentWidget(self.board_page)
        self.page_title.setText("Release Board")
        if hasattr(self, "board_button"):
            self.set_active_nav(self.board_button)
        else:
            self.set_active_nav(self.vinyl_showcase_button)

    def show_library(self):
        self.current_media_type = VINYL
        self._set_collection_badge(VINYL)
        return super().show_library()

    def show_vinyl_showcase(self):
        self.current_media_type = VINYL
        self._set_collection_badge(VINYL)
        return super().show_vinyl_showcase()

    def show_cd_library(self):
        self.current_media_type = CD
        self._set_collection_badge(CD)
        self.pages.setCurrentWidget(self.cd_library_page)
        self.page_title.setText("CD Library")
        self.set_active_nav(self.cd_library_button)
        self.cd_library_page.load_releases()

    def show_cd_showcase_board(self):
        self.current_media_type = CD
        self._set_collection_badge(CD)
        self.pages.setCurrentWidget(self.cd_board_page)
        self.page_title.setText("CD Showcase")
        self.set_active_nav(self.cd_showcase_button)
        self.cd_board_page.load_releases()

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

    def show_discogs(self):
        if self.current_media_type == CD:
            self.pages.setCurrentWidget(self.cd_discogs_page)
            self.page_title.setText("Discogs CD Import")
            self.set_active_nav(self.discogs_button)
        else:
            return super().show_discogs()

    def refresh_after_import(self):
        super().refresh_after_import()
        self.cd_library_page.load_releases()
        self.cd_board_page.load_releases()


def install_cd_mode():
    ensure_media_type_column()
    main_window_module.VinylVaultWindow = CDVinylVaultWindow
