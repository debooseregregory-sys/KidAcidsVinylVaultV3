# ============================================================
# KID ACID'S VINYLVAULT V3
# CD COLLECTION MODE
# ============================================================

from PySide6.QtWidgets import QLabel

from database.database import get_connection
import gui.main_window as main_window_module
from gui.cd_library_page import CDLibraryPage
from gui.cd_showcase_page import CDShowcasePage
from gui.livesets_edit_page import LivesetsEditPage
from gui.livesets_showcase_page import LivesetsShowcasePage
from gui.liveset_detail_page import LivesetDetailPage

VINYL = "VINYL"
CD = "CD"


def ensure_media_type_column():
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
    """CD pages plus an independent Livesets section."""

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
        self.mp3_player.play_started.connect(self.cd_showcase_page.set_active_track)
        self.mp3_player.stopped.connect(self.cd_showcase_page.clear_active_track)
        self.mp3_player.player.playbackStateChanged.connect(self.cd_showcase_page.set_playback_state)

        self.cd_library_button.setEnabled(True)
        self.cd_library_button.setToolTip("CD Library")
        self.cd_library_button.clicked.connect(self.show_cd_library)
        self.cd_showcase_button.setEnabled(True)
        self.cd_showcase_button.setToolTip("CD Showcase")
        self.cd_showcase_button.clicked.connect(self.show_cd_showcase)

        # ----------------------------------------------------
        # LIVESETS: one sidebar section with SHOWCASE FIRST,
        # followed by LIBRARY. Showcase opens a separate detail
        # / player view, while Library remains the edit page.
        # ----------------------------------------------------
        self.livesets_library_page = LivesetsEditPage()
        self.livesets_showcase_page = LivesetsShowcasePage()
        self.liveset_detail_page = LivesetDetailPage()
        self.pages.addWidget(self.livesets_library_page)
        self.pages.addWidget(self.livesets_showcase_page)
        self.pages.addWidget(self.liveset_detail_page)

        self.livesets_library_page.changed.connect(self._reload_livesets_views)
        self.livesets_showcase_page.open_requested.connect(self._open_liveset_detail)
        self.liveset_detail_page.back_requested.connect(self.show_livesets_showcase)
        self.liveset_detail_page.play_mp3.connect(self.player_bar_play)
        self.mp3_player.play_started.connect(self.liveset_detail_page.set_active_track)
        self.mp3_player.stopped.connect(self.liveset_detail_page.clear_active_track)

        sidebar_layout = self.cd_library_button.parentWidget().layout()
        insert_after_cd = sidebar_layout.indexOf(self.cd_library_button) + 1
        sidebar_layout.insertSpacing(insert_after_cd, 14)
        livesets_label = QLabel("LIVESETS")
        livesets_label.setObjectName("collectionSectionLabel")
        sidebar_layout.insertWidget(insert_after_cd + 1, livesets_label)

        label_index = sidebar_layout.indexOf(livesets_label)

        # Requested order: SHOWCASE first, LIBRARY second.
        self.livesets_showcase_button = self.create_nav_button("▶", "Showcase")
        self.livesets_library_button = self.create_nav_button("▣", "Library")
        sidebar_layout.insertWidget(label_index + 1, self.livesets_showcase_button)
        sidebar_layout.insertWidget(label_index + 2, self.livesets_library_button)
        self.livesets_showcase_button.clicked.connect(self.show_livesets_showcase)
        self.livesets_library_button.clicked.connect(self.show_livesets_library)

    def set_active_nav(self, button):
        super().set_active_nav(button)
        for name in ("livesets_showcase_button", "livesets_library_button"):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.setProperty("active", button is btn)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def _reload_livesets_views(self):
        self.livesets_library_page.reload()
        self.livesets_showcase_page.reload()

    def show_livesets_library(self):
        self.livesets_library_page.reload()
        self.pages.setCurrentWidget(self.livesets_library_page)
        self.page_title.setText("Livesets Library")
        self.set_active_nav(self.livesets_library_button)

    def show_livesets_showcase(self):
        self.livesets_showcase_page.reload()
        self.pages.setCurrentWidget(self.livesets_showcase_page)
        self.page_title.setText("Livesets Showcase")
        self.set_active_nav(self.livesets_showcase_button)

    def _open_liveset_detail(self, data):
        self.liveset_detail_page.load_liveset(data)
        self.pages.setCurrentWidget(self.liveset_detail_page)
        self.page_title.setText("Liveset")
        self.set_active_nav(self.livesets_showcase_button)

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
    ensure_media_type_column()
    main_window_module.VinylVaultWindow = CDVinylVaultWindow
