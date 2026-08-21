# ============================================================
# KID ACID'S VINYLVAULT V3
# CD COLLECTION MODE
# ============================================================

from database.database import get_connection
import gui.main_window as main_window_module
from gui.cd_library_page import CDLibraryPage

VINYL = "VINYL"
CD = "CD"


def ensure_media_type_column():
    """Keep the existing vinyl schema compatible with the media filter."""
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
            "UPDATE releases SET media_type='VINYL' "
            "WHERE media_type IS NULL OR TRIM(media_type)=''"
        )
        conn.commit()
    finally:
        conn.close()


OriginalVinylVaultWindow = main_window_module.VinylVaultWindow


class CDVinylVaultWindow(OriginalVinylVaultWindow):
    """Existing VinylVault window extended with the dedicated CD Library."""

    def build_ui(self):
        super().build_ui()

        self.current_media_type = VINYL

        # main_window already creates a CDLibraryPage. Reuse that page
        # instead of creating a second one.
        if not hasattr(self, "cd_library_page"):
            self.cd_library_page = CDLibraryPage()
            self.pages.addWidget(self.cd_library_page)

        self.cd_library_button.setEnabled(True)
        self.cd_library_button.setToolTip("CD Library")
        self.cd_library_button.clicked.connect(self.show_cd_library)

        # CD Showcase is not implemented yet; do not create references to
        # files that do not exist.
        self.cd_showcase_button.setEnabled(False)
        self.cd_showcase_button.setToolTip("CD Showcase wordt later toegevoegd")

    def show_board(self):
        self.pages.setCurrentWidget(self.board_page)
        self.page_title.setText("Release Board")
        if hasattr(self, "board_button"):
            self.set_active_nav(self.board_button)
        elif hasattr(self, "vinyl_showcase_button"):
            self.set_active_nav(self.vinyl_showcase_button)

    def show_library(self):
        self.current_media_type = VINYL
        return super().show_library()

    def show_cd_library(self):
        self.current_media_type = CD
        self.pages.setCurrentWidget(self.cd_library_page)
        self.page_title.setText("CD Library")
        self.set_active_nav(self.cd_library_button)
        self.cd_library_page.load_releases()


def install_cd_mode():
    """Install CD-enabled window before main_window.main() creates it."""
    ensure_media_type_column()
    main_window_module.VinylVaultWindow = CDVinylVaultWindow
