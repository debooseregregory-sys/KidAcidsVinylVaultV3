# ============================================================
# KID ACID'S VINYLVAULT V3
# CD COLLECTION MODE
# ============================================================

from database.database import get_connection
import gui.main_window as main_window_module
from gui.cd_library_page import CDLibraryPage
from gui.cd_showcase_page import CDShowcasePage

VINYL = "VINYL"
CD = "CD"


def ensure_media_type_column():
    conn = get_connection()
    try:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(releases)").fetchall()
        }
        if "media_type" not in columns:
            conn.execute("ALTER TABLE releases ADD COLUMN media_type TEXT DEFAULT 'VINYL'")
        conn.execute(
            "UPDATE releases SET media_type='VINYL' "
            "WHERE media_type IS NULL OR TRIM(media_type)=''"
        )
        conn.commit()
    finally:
        conn.close()


OriginalVinylVaultWindow = main_window_module.VinylVaultWindow


class CDVinylVaultWindow(OriginalVinylVaultWindow):
    """Existing VinylVault window extended with the dedicated CD pages."""

    def build_ui(self):
        super().build_ui()

        self.current_media_type = VINYL
        self.current_cd_id = None

        if not hasattr(self, "cd_library_page"):
            self.cd_library_page = CDLibraryPage()
            self.pages.addWidget(self.cd_library_page)

        self.cd_showcase_page = CDShowcasePage()
        self.pages.addWidget(self.cd_showcase_page)

        self.cd_library_page.cd_selected.connect(self._open_cd_showcase)
        self.cd_showcase_page.back_requested.connect(self.show_cd_showcase)
        self.cd_showcase_page.release_selected.connect(self._open_cd_detail)
        self.cd_showcase_page.play_mp3.connect(self.player_bar_play)

        self.cd_library_button.setEnabled(True)
        self.cd_library_button.setToolTip("CD Library")
        self.cd_library_button.clicked.connect(self.show_cd_library)

        self.cd_showcase_button.setEnabled(True)
        self.cd_showcase_button.setToolTip("CD Showcase")
        self.cd_showcase_button.clicked.connect(self.show_cd_showcase)

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

    def _open_cd_showcase(self, release_id):
        self.current_cd_id = int(release_id)
        self.cd_showcase_page.load_release(self.current_cd_id)
        self.pages.setCurrentWidget(self.cd_showcase_page)
        self.page_title.setText("CD Release")
        self.set_active_nav(self.cd_showcase_button)

    def _open_cd_detail(self, release_id):
        self.current_cd_id = int(release_id)
        self.cd_showcase_page.load_release(self.current_cd_id)
        self.pages.setCurrentWidget(self.cd_showcase_page)
        self.page_title.setText("CD Release")
        self.set_active_nav(self.cd_showcase_button)

    def show_cd_showcase(self):
        self.current_media_type = CD
        self.cd_showcase_page.load_releases()
        self.pages.setCurrentWidget(self.cd_showcase_page)
        self.page_title.setText("CD Showcase")
        self.set_active_nav(self.cd_showcase_button)


def install_cd_mode():
    """Install CD-enabled window before main_window.main() creates it."""
    ensure_media_type_column()
    main_window_module.VinylVaultWindow = CDVinylVaultWindow
