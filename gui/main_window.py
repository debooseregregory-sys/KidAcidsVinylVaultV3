# ============================================================
# KID ACID'S MUSICVAULT V3
# MAIN WINDOW
#
# PROFESSIONAL DESKTOP INTERFACE
# ============================================================

import sys

from gui.app_settings import paint_accent
from database.database import get_connection
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
    QFrame,
    QSizePolicy,
)

from gui.discogs_import_page import DiscogsImportPage
from gui.release_library_page import ReleaseLibraryPage
from gui.release_board_page import ReleaseBoardPage
from gui.release_detail_page import ReleaseDetailPage
from gui.release_showcase_page import ReleaseShowcasePage
from gui.cd_library_page import CDLibraryPage
from gui.player import MP3Player
from gui.mp3_library_page import MP3LibraryPage
from gui.mp3_showcase_page import MP3ShowcasePage
from gui.player_bar import PlayerBar
from gui.mp3_showcase_playback_bridge import install_mp3_showcase_playback_bridge
from gui.settings_page import SettingsPage
from gui.mp3_cutter_dialog import MP3CutterDialog
from gui.mp3_converter_dialog import MP3ConverterDialog
from gui.bpm_analyzer_dialog import BPMAnalyzerDialog


# ============================================================
# DASHBOARD CARD
# ============================================================

class DashboardCard(QFrame):

    def __init__(
        self,
        number,
        label,
        accent=False,
        parent=None
    ):

        super().__init__(parent)

        self.setObjectName(
            "dashboardCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            22,
            20,
            22,
            20
        )

        layout.setSpacing(
            6
        )

        number_label = QLabel(
            str(number)
        )

        number_label.setObjectName(
            "dashboardNumberAccent"
            if accent
            else "dashboardNumber"
        )

        layout.addWidget(
            number_label
        )

        text_label = QLabel(
            label
        )

        text_label.setObjectName(
            "dashboardLabel"
        )

        layout.addWidget(
            text_label
        )


# ============================================================
# SECTION CARD
# ============================================================

class DashboardSection(QFrame):

    def __init__(
        self,
        title,
        description,
        button_text,
        callback,
        parent=None
    ):

        super().__init__(parent)

        self.setObjectName(
            "dashboardSection"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            24,
            22,
            24,
            22
        )

        layout.setSpacing(
            8
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            title_label
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "sectionDescription"
        )

        description_label.setWordWrap(
            True
        )

        layout.addWidget(
            description_label
        )

        layout.addSpacing(
            8
        )

        button = QPushButton(
            button_text
        )

        button.setObjectName(
            "sectionButton"
        )

        button.setMinimumHeight(
            38
        )

        button.clicked.connect(
            callback
        )

        layout.addWidget(
            button,
            0,
            Qt.AlignmentFlag.AlignLeft
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class VinylVaultWindow(QMainWindow):

    def __init__(
        self
    ):

        super().__init__()

        self.setWindowTitle(
            "Kid Acid's MusicVault"
        )

        self.setMinimumSize(
            1200,
            760
        )

        self.resize(
            1500,
            900
        )

        self.current_nav = None

        self.build_ui()
        self._apply_startup_settings()

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(
        self
    ):

        central = QWidget()

        central.setObjectName(
            "centralWidget"
        )

        self.setCentralWidget(
            central
        )

        main_layout = QHBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = QWidget()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            250
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            18,
            22,
            18,
            18
        )

        sidebar_layout.setSpacing(
            8
        )

        # ====================================================
        # BRAND
        # ====================================================

        brand_container = QWidget()

        brand_layout = QVBoxLayout(
            brand_container
        )

        brand_layout.setContentsMargins(
            8,
            0,
            8,
            0
        )

        brand_layout.setSpacing(
            2
        )

        brand_small = QLabel(
            "KID ACID'S"
        )

        brand_small.setObjectName(
            "brandSmall"
        )

        brand_layout.addWidget(
            brand_small
        )

        brand_title = QLabel(
            "MUSICVAULT"
        )

        brand_title.setObjectName(
            "brandTitle"
        )

        brand_layout.addWidget(
            brand_title
        )

        brand_version = QLabel(
            "V3  •  MUSIC COLLECTION"
        )

        brand_version.setObjectName(
            "brandVersion"
        )

        brand_layout.addWidget(
            brand_version
        )

        sidebar_layout.addWidget(
            brand_container
        )

        sidebar_layout.addSpacing(
            28
        )

        # ====================================================
        # COLLECTION NAVIGATION
        # ====================================================

        navigation_label = QLabel("COLLECTIONS")
        navigation_label.setObjectName("navigationLabel")
        sidebar_layout.addWidget(navigation_label)
        sidebar_layout.addSpacing(4)

        # ----------------------------------------------------
        # VINYL
        # ----------------------------------------------------

        vinyl_label = QLabel("VINYL")
        vinyl_label.setObjectName("collectionSectionLabel")
        sidebar_layout.addWidget(vinyl_label)

        self.vinyl_showcase_button = self.create_nav_button("◉", "Showcase")
        self.vinyl_showcase_button.clicked.connect(self.show_vinyl_showcase)
        sidebar_layout.addWidget(self.vinyl_showcase_button)

        self.library_button = self.create_nav_button("▣", "Release Library")
        self.library_button.clicked.connect(self.show_library)
        sidebar_layout.addWidget(self.library_button)

        # ----------------------------------------------------
        # MP3
        # ----------------------------------------------------

        mp3_label = QLabel("MP3")
        mp3_label.setObjectName("collectionSectionLabel")
        sidebar_layout.addSpacing(14)
        sidebar_layout.addWidget(mp3_label)

        self.mp3_showcase_button = self.create_nav_button("♫", "Showcase")
        self.mp3_showcase_button.clicked.connect(self.show_mp3_showcase)
        sidebar_layout.addWidget(self.mp3_showcase_button)

        self.mp3_button = self.create_nav_button("▤", "MP3 Library")
        self.mp3_button.clicked.connect(self.show_mp3_library)
        sidebar_layout.addWidget(self.mp3_button)

        # ----------------------------------------------------
        # CD
        # ----------------------------------------------------

        cd_label = QLabel("CD")
        cd_label.setObjectName("collectionSectionLabel")
        sidebar_layout.addSpacing(14)
        sidebar_layout.addWidget(cd_label)

        self.cd_showcase_button = self.create_nav_button("●", "Showcase")
        self.cd_showcase_button.setEnabled(False)
        self.cd_showcase_button.setToolTip("CD-module wordt toegevoegd zodra de CD-collectielijst is ingevoerd.")
        sidebar_layout.addWidget(self.cd_showcase_button)

        self.cd_library_button = self.create_nav_button("▤", "CD Library")
        self.cd_library_button.clicked.connect(self.show_cd_library)
        sidebar_layout.addWidget(self.cd_library_button)

        # ----------------------------------------------------
        # TOOLS
        # ----------------------------------------------------

        tools_label = QLabel("TOOLS")
        tools_label.setObjectName("navigationLabel")
        sidebar_layout.addSpacing(22)
        sidebar_layout.addWidget(tools_label)

        self.discogs_button = self.create_nav_button("◈", "Discogs Import")
        self.discogs_button.clicked.connect(self.show_discogs)
        sidebar_layout.addWidget(self.discogs_button)

        self.settings_button = self.create_nav_button("⚙", "Settings")
        self.settings_button.clicked.connect(self.show_settings)
        sidebar_layout.addWidget(self.settings_button)

        self.mp3_cutter_button = self.create_nav_button("✂", "MP3 Cutter")
        self.mp3_cutter_button.clicked.connect(self.open_mp3_cutter_standalone)
        sidebar_layout.addWidget(self.mp3_cutter_button)

        self.mp3_converter_button = self.create_nav_button("⇄", "MP3 Converter")
        self.mp3_converter_button.clicked.connect(self.open_mp3_converter_standalone)
        sidebar_layout.addWidget(self.mp3_converter_button)

        self.bpm_analyzer_button = self.create_nav_button("♫", "BPM Analysator")
        self.bpm_analyzer_button.clicked.connect(self.open_bpm_analyzer_standalone)
        sidebar_layout.addWidget(self.bpm_analyzer_button)

        # ====================================================
        # SIDEBAR FOOTER
        # ====================================================

        footer = QLabel(
            "MUSIC COLLECTION  •  KID ACID"
        )

        footer.setObjectName(
            "sidebarFooter"
        )

        footer.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        sidebar_layout.addWidget(
            footer
        )

        # ====================================================
        # RIGHT SIDE
        # ====================================================

        right_container = QWidget()

        right_container.setObjectName(
            "rightContainer"
        )

        right_layout = QVBoxLayout(
            right_container
        )

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(
            0
        )

        # ====================================================
        # TOP BAR
        # ====================================================

        top_bar = QWidget()

        top_bar.setObjectName(
            "topBar"
        )

        top_bar.setFixedHeight(
            74
        )

        top_layout = QHBoxLayout(
            top_bar
        )

        top_layout.setContentsMargins(
            28,
            0,
            28,
            0
        )

        top_layout.setSpacing(
            12
        )

        self.page_title = QLabel(
            "Dashboard"
        )

        self.page_title.setObjectName(
            "topPageTitle"
        )

        top_layout.addWidget(
            self.page_title
        )

        top_layout.addStretch()

        collection_label = QLabel(
            "MUSIC COLLECTION"
        )

        collection_label.setObjectName(
            "collectionBadge"
        )

        top_layout.addWidget(
            collection_label
        )

        right_layout.addWidget(
            top_bar
        )

        # ====================================================
        # PAGE STACK
        # ====================================================

        self.pages = QStackedWidget()

        self.pages.setObjectName(
            "pageStack"
        )

        # ====================================================
        # HOME
        # ====================================================

        self.home_page = self.build_home_page()

        self.pages.addWidget(
            self.home_page
        )

        # ====================================================
        # RELEASE BOARD
        # ====================================================

        self.board_page = ReleaseBoardPage()

        self.board_page.open_release.connect(
            self.show_showcase
        )

        self.board_page.play_mp3.connect(
            self.player_bar_play
        )

        self.pages.addWidget(
            self.board_page
        )
        # ====================================================
        # RELEASE SHOWCASE
        # ====================================================

        self.showcase_page = ReleaseShowcasePage()

        self.showcase_page.back_requested.connect(
            self.show_board
        )

        self.showcase_page.edit_requested.connect(
            self.open_release
        )

        self.showcase_page.play_mp3.connect(
            self.player_bar_play
        )

        self.pages.addWidget(
            self.showcase_page
        )


        # ====================================================
        # DASHBOARD
        # ====================================================

        self.home_button = self.create_nav_button(
            "⌂",
            "Dashboard"
        )

        self.home_button.clicked.connect(
            self.show_home
        )

        sidebar_layout.addWidget(
            self.home_button
        )

        # ====================================================
        # VINYL
        # ====================================================

        vinyl_label = QLabel("VINYL")
        vinyl_label.setObjectName("navigationLabel")
        sidebar_layout.addSpacing(12)
        sidebar_layout.addWidget(vinyl_label)

        # ====================================================
        # RELEASE LIBRARY
        # ====================================================

        self.library_page = ReleaseLibraryPage()

        self.library_page.release_selected.connect(
            self.open_release
        )

        self.pages.addWidget(
            self.library_page
        )

        # ====================================================
        # RELEASE DETAIL
        # ====================================================

        self.detail_page = ReleaseDetailPage()

        self.detail_page.back_requested.connect(
            self.show_library
        )

        self.detail_page.release_deleted.connect(
            self.library_page.load_releases
        )

        self.detail_page.play_mp3.connect(
            self.player_bar_play
        )

        self.pages.addWidget(
            self.detail_page
        )

        # ====================================================
        # DISCOGS
        # ====================================================

        self.discogs_page = DiscogsImportPage()

        # ====================================================
        # MP3 LIBRARY
        # ====================================================

        self.mp3_library_page = MP3LibraryPage()

        self.mp3_library_page.play_mp3.connect(
            self.player_bar_play
        )

        self.pages.addWidget(
            self.mp3_library_page
        )

        self.discogs_page.import_finished.connect(
            self.refresh_after_import
        )

        self.pages.addWidget(
            self.discogs_page
        )

        # ====================================================
        # MP3 SHOWCASE
        # ====================================================

        self.mp3_showcase_page = MP3ShowcasePage()

        # ====================================================
        # CD LIBRARY
        # ====================================================

        self.cd_library_page = CDLibraryPage()
        self.pages.addWidget(
            self.cd_library_page
        )

        # ====================================================
        # SETTINGS
        # ====================================================

        self.settings_page = SettingsPage()
        self.pages.addWidget(
            self.settings_page
        )

        install_mp3_showcase_playback_bridge()

        self.mp3_showcase_page.play_mp3.connect(
            self.player_bar_play
        )

        self.pages.addWidget(
            self.mp3_showcase_page
        )

        right_layout.addWidget(
            self.pages,
            1
        )

        # ====================================================
        # PLAYER
        # ====================================================

        self.mp3_player = MP3Player()

        self.player_bar = PlayerBar(
            self.mp3_player
        )

        self._player_bar_ready = True
        self.player_bar.setFixedHeight(
            78
        )

        right_layout.addWidget(
            self.player_bar
        )

        # ====================================================
        # ADD SIDEBAR + RIGHT SIDE
        # ====================================================

        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            right_container,
            1
        )

        # ====================================================
        # STYLE
        # ====================================================

        self.apply_style()

        # ====================================================
        # START
        # ====================================================

        self.set_active_nav(
            self.home_button
        )

        self.pages.setCurrentWidget(
            self.home_page
        )

    # ========================================================
    # SETTINGS
    # ========================================================


    def _settings_store(self):
        return QSettings("Kid Acid", "MusicVault")

    def _apply_startup_settings(self):
        """Restore window geometry, volume and open the preferred start page."""
        settings = self._settings_store()

        if settings.value("remember_window_state", True, type=bool):
            geometry = settings.value("window_geometry")
            if geometry is not None:
                try:
                    self.restoreGeometry(geometry)
                except Exception:
                    pass
            state = settings.value("window_state")
            if state is not None:
                try:
                    self.restoreState(state)
                except Exception:
                    pass

        # Open preferred page after UI is ready
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._open_startup_page)

    def _open_startup_page(self):
        settings = self._settings_store()
        if settings.value("remember_last_page", True, type=bool):
            page = str(settings.value("last_page", "") or "").strip()
        else:
            page = str(settings.value("start_page", "Dashboard") or "Dashboard")
        self._navigate_to_named_page(page)

    def _navigate_to_named_page(self, page):
        page = str(page or "Dashboard").strip()
        mapping = {
            "Dashboard": "show_home",
            "Home": "show_home",
            "Release Board": "show_board",
            "Board": "show_board",
            "Release Library": "show_library",
            "Library": "show_library",
            "Vinyl Showcase": "show_vinyl_showcase",
            "Showcase": "show_vinyl_showcase",
            "CD Library": "show_cd_library",
            "CD Showcase": "show_cd_library",
            "MP3 Library": "show_mp3_library",
            "MP3 Showcase": "show_mp3_showcase",
            "Discogs Import": "show_discogs",
            "Discogs": "show_discogs",
            "Settings": "show_settings",
        }
        method_name = mapping.get(page, "show_home")
        method = getattr(self, method_name, None)
        if callable(method):
            try:
                method()
            except Exception as exc:
                print("Startup navigation failed:", page, exc)
                if method_name != "show_home" and hasattr(self, "show_home"):
                    self.show_home()

    def _remember_current_page(self, name):
        settings = self._settings_store()
        if settings.value("remember_last_page", True, type=bool):
            settings.setValue("last_page", name)

    def closeEvent(self, event):
        settings = self._settings_store()
        if settings.value("remember_window_state", True, type=bool):
            settings.setValue("window_geometry", self.saveGeometry())
            settings.setValue("window_state", self.saveState())
        # Best-effort: store last title as page hint
        try:
            title = str(self.page_title.text() or "").strip()
            if title:
                settings.setValue("last_page", title)
        except Exception:
            pass
        super().closeEvent(event)


    def show_settings(self):
        self.pages.setCurrentWidget(self.settings_page)
        self.page_title.setText("Settings")
        self._remember_current_page("Settings")
        self.set_active_nav(self.settings_button)

    # ========================================================
    # CD LIBRARY
    # ========================================================

    def show_cd_library(self):
        self.pages.setCurrentWidget(self.cd_library_page)
        self.page_title.setText("CD Library")
        self._remember_current_page("CD Library")
        self.set_active_nav(self.cd_library_button)
        if hasattr(self.cd_library_page, "load_releases"):
            self.cd_library_page.load_releases()

    # ========================================================
    # CREATE NAV BUTTON
    # ========================================================

    def create_nav_button(
        self,
        icon,
        text
    ):

        button = QPushButton()

        button.setObjectName(
            "navButton"
        )

        button.setMinimumHeight(
            48
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        layout = QHBoxLayout(
            button
        )

        layout.setContentsMargins(
            12,
            0,
            12,
            0
        )

        layout.setSpacing(
            12
        )

        icon_label = QLabel(
            icon
        )

        icon_label.setObjectName(
            "navIcon"
        )

        icon_label.setFixedWidth(
            24
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            icon_label
        )

        text_label = QLabel(
            text
        )

        text_label.setObjectName(
            "navText"
        )

        layout.addWidget(
            text_label
        )

        layout.addStretch()

        return button

    # ========================================================
    # BUILD HOME PAGE
    # ========================================================

    def build_home_page(
        self
    ):

        page = QWidget()

        page.setObjectName(
            "homePage"
        )

        layout = QVBoxLayout(
            page
        )

        layout.setContentsMargins(
            36,
            32,
            36,
            32
        )

        layout.setSpacing(
            22
        )

        # ====================================================
        # HERO
        # ====================================================

        hero = QWidget()

        hero_layout = QVBoxLayout(
            hero
        )

        hero_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        hero_layout.setSpacing(
            5
        )

        welcome = QLabel(
            "Welcome back, Kid Acid."
        )

        welcome.setObjectName(
            "heroTitle"
        )

        hero_layout.addWidget(
            welcome
        )

        subtitle = QLabel(
            "Beheer je volledige fysieke vinylcollectie vanuit één professionele omgeving."
        )

        subtitle.setObjectName(
            "heroSubtitle"
        )

        subtitle.setWordWrap(
            True
        )

        hero_layout.addWidget(
            subtitle
        )

        layout.addWidget(
            hero
        )

        # ====================================================
        # STATS
        # ====================================================

        stats = QHBoxLayout()

        stats.setSpacing(
            14
        )

        stats.addWidget(
            DashboardCard(
                "5.582",
                "RELEASES",
                True
            )
        )

        stats.addWidget(
            DashboardCard(
                "15.683",
                "TRACKS"
            )
        )

        stats.addWidget(
            DashboardCard(
                "33.409",
                "MP3 FILES"
            )
        )

        stats.addWidget(
            DashboardCard(
                "3.214",
                "MP3 KOPPELINGEN"
            )
        )

        layout.addLayout(
            stats
        )

        # ====================================================
        # MAIN ACTIONS
        # ====================================================

        action_layout = QHBoxLayout()

        action_layout.setSpacing(
            14
        )

        library_section = DashboardSection(
            "Release Library",
            "Bekijk, zoek en beheer al je fysieke releases. Open een release om tracks, MP3's, Discogs en opslaggegevens te beheren.",
            "OPEN RELEASE LIBRARY",
            self.show_library
        )

        action_layout.addWidget(
            library_section,
            1
        )

        discogs_section = DashboardSection(
            "Discogs Import",
            "Haal gecontroleerde releasegegevens uit Discogs op en verrijk je bestaande collectie.",
            "OPEN DISCOGS",
            self.show_discogs
        )

        action_layout.addWidget(
            discogs_section,
            1
        )

        layout.addLayout(
            action_layout
        )

        # ====================================================
        # MAIN ACTIONS - ROW 2
        # ====================================================
        action_layout_2 = QHBoxLayout()
        action_layout_2.setSpacing(
            14
        )
        cd_section = DashboardSection(
            "CD Library",
            "Beheer je CD-collectie: releases, tracks, hoezen en MP3-koppelingen op dezelfde manier als vinyl.",
            "OPEN CD LIBRARY",
            self.show_cd_library
        )
        action_layout_2.addWidget(
            cd_section,
            1
        )
        mp3_section = DashboardSection(
            "MP3 Library",
            "Doorzoek en beheer alle digitale audiobestanden die aan je collectie gekoppeld kunnen worden.",
            "OPEN MP3 LIBRARY",
            self.show_mp3_library
        )
        action_layout_2.addWidget(
            mp3_section,
            1
        )
        livesets_section = DashboardSection(
            "Livesets",
            "Bekijk en beheer je verzameling livesets, los van je vinyl- en CD-collectie.",
            "OPEN LIVESETS",
            lambda: self.show_livesets_showcase()
        )
        action_layout_2.addWidget(
            livesets_section,
            1
        )
        layout.addLayout(
            action_layout_2
        )
        # ====================================================
        # MAIN ACTIONS - ROW 3
        # ====================================================
        action_layout_3 = QHBoxLayout()
        action_layout_3.setSpacing(
            14
        )
        bpm_section = DashboardSection(
            "BPM Analysator",
            "Loopt de hele collectie af en analyseert automatisch het BPM van elke track met een gekoppelde MP3, en zet het resultaat ook in de Notities.",
            "OPEN BPM ANALYSATOR",
            self.open_bpm_analyzer_standalone
        )
        action_layout_3.addWidget(
            bpm_section,
            1
        )
        layout.addLayout(
            action_layout_3
        )
        # ====================================================
        # COLLECTION HEALTH
        # ====================================================
        try:
            health_connection = get_connection()
            missing_mp3 = health_connection.execute(
                "SELECT COUNT(*) FROM tracks WHERE id NOT IN (SELECT track_id FROM track_mp3)"
            ).fetchone()[0]
            missing_cover = health_connection.execute(
                "SELECT COUNT(*) FROM releases WHERE cover IS NULL OR cover = \'\'"
            ).fetchone()[0]
            missing_discogs = health_connection.execute(
                "SELECT COUNT(*) FROM releases WHERE discogs IS NULL OR discogs = \'\'"
            ).fetchone()[0]
            health_connection.close()
        except Exception:
            missing_mp3 = 0
            missing_cover = 0
            missing_discogs = 0
        health_panel = QFrame()
        health_panel.setObjectName(
            "healthPanel"
        )
        health_outer = QVBoxLayout(
            health_panel
        )
        health_outer.setContentsMargins(
            20, 18, 20, 18
        )
        health_outer.setSpacing(
            10
        )
        health_title = QLabel(
            "COLLECTIE-GEZONDHEID"
        )
        health_title.setObjectName(
            "healthTitle"
        )
        health_outer.addWidget(
            health_title
        )
        health_row = QHBoxLayout()
        health_row.setSpacing(
            12
        )
        health_mp3_button = QPushButton(
            f"{missing_mp3}  Tracks zonder MP3-koppeling"
        )
        health_mp3_button.setObjectName(
            "healthTile"
        )
        health_mp3_button.clicked.connect(
            self.show_library
        )
        health_row.addWidget(
            health_mp3_button
        )
        health_cover_button = QPushButton(
            f"{missing_cover}  Releases zonder cover"
        )
        health_cover_button.setObjectName(
            "healthTile"
        )
        health_cover_button.clicked.connect(
            self.show_library
        )
        health_row.addWidget(
            health_cover_button
        )
        health_discogs_button = QPushButton(
            f"{missing_discogs}  Releases zonder Discogs-koppeling"
        )
        health_discogs_button.setObjectName(
            "healthTile"
        )
        health_discogs_button.clicked.connect(
            self.show_library
        )
        health_row.addWidget(
            health_discogs_button
        )
        health_outer.addLayout(
            health_row
        )
        health_panel.setStyleSheet(
            paint_accent(
                "QFrame#healthPanel { background: #121217; border: 1px solid #292933; border-radius: 12px; } "
                "QLabel#healthTitle { color: #9b9ba6; font-size: 12px; font-weight: 900; letter-spacing: 2px; } "
                "QPushButton#healthTile { background: #18181f; color: #f2f2f5; border: 1px solid #30303a; "
                "border-radius: 8px; padding: 12px 14px; font-size: 12px; font-weight: 700; text-align: left; } "
                "QPushButton#healthTile:hover { background: #24242c; border-color: #d84b91; color: #d84b91; }"
            )
        )
        layout.addWidget(
            health_panel
        )
        # ====================================================
        # STATUS
        # ====================================================

        status = QFrame()

        status.setObjectName(
            "statusPanel"
        )

        status_layout = QHBoxLayout(
            status
        )

        status_layout.setContentsMargins(
            20,
            16,
            20,
            16
        )

        status_icon = QLabel(
            "●"
        )

        status_icon.setObjectName(
            "statusIcon"
        )

        status_layout.addWidget(
            status_icon
        )

        status_text = QLabel(
            "MusicVault database actief"
        )

        status_text.setObjectName(
            "statusTitle"
        )

        status_layout.addWidget(
            status_text
        )

        status_layout.addStretch()

        database_text = QLabel(
            "Lokale collectie - Database verbonden"
        )

        database_text.setObjectName(
            "statusText"
        )

        status_layout.addWidget(
            database_text
        )

        layout.addWidget(
            status
        )

        layout.addStretch()
        # ====================================================
        # DECORATIVE FOOTER
        # ====================================================
        gradient_band = QFrame()
        gradient_band.setFixedHeight(
            4
        )
        gradient_band.setStyleSheet(
            paint_accent(
                "QFrame { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0 transparent, stop:0.5 #d84b91, stop:1 transparent); "
                "border: none; }"
            )
        )
        layout.addWidget(
            gradient_band
        )
        footer = QFrame()
        footer.setObjectName(
            "dashboardFooter"
        )
        footer_layout = QHBoxLayout(
            footer
        )
        footer_layout.setContentsMargins(
            20, 18, 20, 18
        )
        footer_layout.setSpacing(
            14
        )
        vinyl_deco = QLabel()
        vinyl_deco.setObjectName(
            "vinylDeco"
        )
        vinyl_deco.setFixedSize(
            52,
            52
        )
        vinyl_deco.setStyleSheet(
            paint_accent(
                "QLabel#vinylDeco { "
                "border-radius: 26px; "
                "background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, "
                "stop:0 #d84b91, stop:0.18 #d84b91, stop:0.19 #0e0e12, stop:0.32 #0e0e12, "
                "stop:0.33 #1c1c22, stop:0.55 #1c1c22, stop:0.56 #0e0e12, stop:1 #0e0e12); "
                "border: 2px solid #2a2a33; }"
            )
        )
        footer_layout.addWidget(
            vinyl_deco
        )
        footer_text_layout = QVBoxLayout()
        footer_text_layout.setSpacing(
            2
        )
        footer_title = QLabel(
            "KID ACIDS MUSICVAULT"
        )
        footer_title.setObjectName(
            "footerTitle"
        )
        footer_text_layout.addWidget(
            footer_title
        )
        footer_tagline = QLabel(
            "Handgemaakt voor een serieuze vinyl-, CD- en MP3-collectie."
        )
        footer_tagline.setObjectName(
            "footerTagline"
        )
        footer_text_layout.addWidget(
            footer_tagline
        )
        footer_layout.addLayout(
            footer_text_layout
        )
        footer_layout.addStretch()
        footer_version = QLabel(
            "V3"
        )
        footer_version.setObjectName(
            "footerVersion"
        )
        footer_layout.addWidget(
            footer_version
        )
        footer.setStyleSheet(
            "QFrame#dashboardFooter { background: #0e0e12; border-top: 1px solid #22222a; } "
            "QLabel#footerTitle { color: #9b9ba6; font-size: 12px; font-weight: 900; letter-spacing: 2px; } "
            "QLabel#footerTagline { color: #5c5c66; font-size: 11px; } "
            "QLabel#footerVersion { color: #d84b91; font-size: 20px; font-weight: 900; letter-spacing: 1px; }"
        )
        layout.addWidget(
            footer
        )

        return page

    # ========================================================
    # ACTIVE NAVIGATION
    # ========================================================

    def set_active_nav(
        self,
        button
    ):

        buttons = [
            self.home_button,            self.library_button,
            self.vinyl_showcase_button,
            self.discogs_button,
            self.settings_button,
        ]

        for item in buttons:

            item.setProperty(
                "active",
                item is button
            )

            item.style().unpolish(
                item
            )

            item.style().polish(
                item
            )

        self.current_nav = button

    # ========================================================
    # VINYL SHOWCASE
    # ========================================================

    def show_vinyl_showcase(self):
        self.pages.setCurrentWidget(self.board_page)
        self.page_title.setText("Vinyl Showcase")
        self.set_active_nav(self.vinyl_showcase_button)
        if hasattr(self.board_page, "load_releases"):
            self.board_page.load_releases()
    def show_mp3_showcase(self):
        self.pages.setCurrentWidget(self.mp3_showcase_page)
        self.page_title.setText("MP3 Showcase")
        self.set_active_nav(self.mp3_showcase_button)
        if hasattr(self.mp3_showcase_page, "search"):
            self.mp3_showcase_page.search.setFocus()

    # ========================================================
    # MP3 LIBRARY
    # ========================================================

    def show_mp3_library(self):
        self.pages.setCurrentWidget(self.mp3_library_page)
        self.page_title.setText("MP3 Library")
        self.set_active_nav(self.mp3_button)

    # ========================================================
    # HOME
    # ========================================================

    def show_home(
        self
    ):

        self.pages.setCurrentWidget(
            self.home_page
        )

        self.page_title.setText(
            "Dashboard"
        )

        self.set_active_nav(
            self.home_button
        )

    # ========================================================
    # RELEASE BOARD
    # ========================================================

    def show_board(
        self
    ):

        self.pages.setCurrentWidget(
            self.board_page
        )

        self.page_title.setText(
            "Release Board"
        )

        self.set_active_nav(
            self.vinyl_showcase_button
        )

    # ========================================================
    # RELEASE LIBRARY
    # ========================================================

    def show_library(
        self
    ):

        # Navigeren moet direct zijn. De volledige database wordt
        # alleen opnieuw geladen via de knop VERWIEUW of na een
        # expliciete databasewijziging.
        self.library_page.load_releases()

        self.pages.setCurrentWidget(
            self.library_page
        )

        search_text = (
            self.library_page.search_input.text()
        )

        if search_text:
            self.library_page.filter_releases(
                search_text
            )

        self.page_title.setText(
            "Release Library"
        )

        self.set_active_nav(
            self.library_button
        )

    # ========================================================
    # OPEN RELEASE
    # ========================================================

    def open_release(
        self,
        release_id,
        release_ids=None
    ):
        if release_ids is None:
            release_ids = self.library_page.visible_release_ids()
        self.detail_page.load_release(
            release_id
        )
        self.detail_page.set_navigation_ids(
            release_ids
        )

        self.pages.setCurrentWidget(
            self.detail_page
        )

        self.page_title.setText(
            "Release"
        )

        self.set_active_nav(
            self.library_button
        )

    # ========================================================
    # MP3 CUTTER (STANDALONE)
    # ========================================================

    def open_mp3_cutter_standalone(self):

        dialog = MP3CutterDialog(
            initial_path=None,
            parent=self
        )

        dialog.exec()

    # ========================================================
    # MP3 CONVERTER (STANDALONE)
    # ========================================================

    def open_mp3_converter_standalone(self):

        dialog = MP3ConverterDialog(
            initial_folder=None,
            parent=self
        )

        dialog.exec()

    # ========================================================
    # BPM ANALYSATOR (STANDALONE)
    # ========================================================

    def open_bpm_analyzer_standalone(self):

        dialog = BPMAnalyzerDialog(
            parent=self
        )

        dialog.exec()

    # ========================================================
    # RELEASE SHOWCASE
    # ========================================================

    def show_showcase(
        self,
        release_id
    ):

        self.showcase_page.load_release(
            release_id
        )

        self.pages.setCurrentWidget(
            self.showcase_page
        )

        self.page_title.setText(
            "Release"
        )

        self.set_active_nav(
            self.vinyl_showcase_button
        )

    # ========================================================
    # MP3 LIBRARY
    # ========================================================

    def show_mp3_library(self):

        self.mp3_library_page.load_data()

        self.pages.setCurrentWidget(
            self.mp3_library_page
        )

        self.page_title.setText(
            "MP3 Library"
        )

        self.set_active_nav(
            self.mp3_button
        )

    # ========================================================
    # DISCOGS
    # ========================================================

    def show_discogs(
        self
    ):

        self.pages.setCurrentWidget(
            self.discogs_page
        )

        self.page_title.setText(
            "Discogs Import"
        )

        self.set_active_nav(
            self.discogs_button
        )

        if hasattr(
            self.discogs_page,
            "release_id_input"
        ):

            self.discogs_page.release_id_input.setFocus()

    # ========================================================
    # MP3 SHOWCASE
    # ========================================================

    def show_mp3_showcase(
        self
    ):

        self.pages.setCurrentWidget(
            self.mp3_showcase_page
        )

        self.page_title.setText(
            "MP3 Showcase"
        )

        if hasattr(self, "mp3_showcase_button"):
            self.set_active_nav(
                self.mp3_showcase_button
            )

    # ========================================================
    # PLAY MP3
    # ========================================================

    def player_bar_play(
        self,
        path
    ):

        self.player_bar.play_file(
            path
        )

    # ========================================================
    # AFTER IMPORT
    # ========================================================

    def refresh_after_import(
        self
    ):

        print(
            "MusicVault: database gewijzigd."
        )

        self.library_page.load_releases()

    # ========================================================
    # STYLE
    # ========================================================

    def apply_style(
        self
    ):

        self.setStyleSheet(paint_accent("""
            /* ==================================================
               GLOBAL
               ================================================== */

            QMainWindow {
                background-color: #0b0b0f;
            }

            QWidget {
                background-color: #0b0b0f;
                color: #f2f2f5;
                font-family: "Segoe UI";
            }

            QWidget#centralWidget {
                background-color: #0b0b0f;
            }

            QWidget#rightContainer {
                background-color: #0b0b0f;
            }

            QStackedWidget#pageStack {
                background-color: #0b0b0f;
            }

            /* ==================================================
               SIDEBAR
               ================================================== */

            QWidget#sidebar {
                background-color: #111116;
                border-right: 1px solid #24242d;
            }

            QLabel#brandSmall {
                background: transparent;
                color: #a9a9b4;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 2px;
            }

            QLabel#brandTitle {
                background: transparent;
                color: #ffffff;
                font-size: 25px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#brandVersion {
                background: transparent;
                color: #d84b91;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QLabel#navigationLabel {
                background: transparent;
                color: #666672;
                font-size: 10px;
                font-weight: bold;
                padding-left: 12px;
                letter-spacing: 1.5px;
            }

            QLabel#collectionSectionLabel {
                background: transparent;
                color: #d84b91;
                font-size: 10px;
                font-weight: 900;
                padding-left: 12px;
                margin-top: 2px;
                letter-spacing: 1.8px;
            }

            QLabel#sidebarFooter {
                background: transparent;
                color: #4d4d57;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
                padding-top: 8px;
            }

            /* ==================================================
               NAVIGATION
               ================================================== */

            QPushButton#navButton {
                background-color: transparent;
                color: #ffffff;
                border: 1px solid transparent;
                border-radius: 8px;
                text-align: left;
                min-height: 48px;
            }

            QPushButton#navButton:hover {
                background-color: #1b1820;
                color: #ffffff;
                border: 1px solid #2d2731;
            }

            QPushButton#navButton[active="true"] {
                background-color: #271522;
                color: #ffffff;
                border: 1px solid #5d2947;
            }

            QLabel#navIcon {
                background: transparent;
                color: #777783;
                font-size: 18px;
                font-weight: bold;
            }

            QPushButton#navButton[active="true"] QLabel#navIcon {
                color: #e05299;
            }

            QLabel#navText {
                background: transparent;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
            }

            /* ==================================================
               TOP BAR
               ================================================== */

            QWidget#topBar {
                background-color: #0f0f14;
                border-bottom: 1px solid #24242d;
            }

            QLabel#topPageTitle {
                background: transparent;
                color: #ffffff;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#collectionBadge {
                background-color: #18131a;
                color: #d84b91;
                border: 1px solid #3f2635;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            /* ==================================================
               DASHBOARD
               ================================================== */

            QWidget#homePage {
                background-color: #0b0b0f;
            }

            QLabel#heroTitle {
                background: transparent;
                color: #ffffff;
                font-size: 30px;
                font-weight: 750;
            }

            QLabel#heroSubtitle {
                background: transparent;
                color: #858590;
                font-size: 13px;
            }

            /* ==================================================
               DASHBOARD CARDS
               ================================================== */

            QFrame#dashboardCard {
                background-color: #121218;
                border: 1px solid #25252f;
                border-radius: 10px;
            }

            QFrame#dashboardCard:hover {
                border: 1px solid #493040;
                background-color: #15151c;
            }

            QLabel#dashboardNumber {
                background: transparent;
                color: #ffffff;
                font-size: 27px;
                font-weight: 750;
            }

            QLabel#dashboardNumberAccent {
                background: transparent;
                color: #e05299;
                font-size: 27px;
                font-weight: 750;
            }

            QLabel#dashboardLabel {
                background: transparent;
                color: #686873;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            /* ==================================================
               DASHBOARD SECTIONS
               ================================================== */

            QFrame#dashboardSection {
                background-color: #121218;
                border: 1px solid #25252f;
                border-radius: 10px;
            }

            QLabel#sectionTitle {
                background: transparent;
                color: #ffffff;
                font-size: 17px;
                font-weight: 700;
            }

            QLabel#sectionDescription {
                background: transparent;
                color: #858590;
                font-size: 12px;
                line-height: 1.4;
            }

            QPushButton#sectionButton {
                background-color: #1d1920;
                color: #d84b91;
                border: 1px solid #4b2a3d;
                border-radius: 6px;
                padding: 7px 13px;
                font-size: 10px;
                font-weight: bold;
            }

            QPushButton#sectionButton:hover {
                background-color: #d84b91;
                color: #ffffff;
                border: 1px solid #d84b91;
            }

            /* ==================================================
               STATUS
               ================================================== */

            QFrame#statusPanel {
                background-color: #10151a;
                border: 1px solid #23352b;
                border-radius: 8px;
            }

            QLabel#statusIcon {
                background: transparent;
                color: #65c47a;
                font-size: 13px;
            }

            QLabel#statusTitle {
                background: transparent;
                color: #b9c6bc;
                font-size: 12px;
                font-weight: bold;
            }

            QLabel#statusText {
                background: transparent;
                color: #626b65;
                font-size: 11px;
            }

            /* ==================================================
               GENERAL BUTTONS
               ================================================== */

            QPushButton {
                background-color: #1b1b22;
                color: #ededf2;
                border: 1px solid #30303a;
                border-radius: 7px;
                padding: 8px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #29202a;
                border: 1px solid #d84b91;
            }

            QPushButton:pressed {
                background-color: #d84b91;
                color: #ffffff;
            }

            QPushButton:disabled {
                background-color: #15151a;
                color: #484851;
                border: 1px solid #22222a;
            }

            /* ==================================================
               INPUTS
               ================================================== */

            QLineEdit {
                background-color: #17171d;
                color: #ffffff;
                border: 1px solid #30303a;
                border-radius: 7px;
                padding: 8px 11px;
                selection-background-color: #8b315e;
                selection-color: #ffffff;
            }

            QLineEdit:focus {
                border: 1px solid #d84b91;
            }

            /* ==================================================
               SCROLLBARS
               ================================================== */

            QScrollBar:vertical {
                background-color: #101014;
                width: 10px;
                border: none;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background-color: #363640;
                border-radius: 5px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #d84b91;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar:horizontal {
                background-color: #101014;
                height: 10px;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background-color: #363640;
                border-radius: 5px;
                min-width: 35px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #d84b91;
            }
            """))


# ============================================================
# START
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Kid Acid's MusicVault"
    )

    app.setApplicationDisplayName(
        "Kid Acid's MusicVault"
    )

    app.setStyle(
        "Fusion"
    )

    window = VinylVaultWindow()

    # Maximized only when no saved geometry
    settings = QSettings("Kid Acid", "MusicVault")
    has_geometry = settings.value("window_geometry") is not None and settings.value("remember_window_state", True, type=bool)
    if not has_geometry:
        window.showMaximized()
    window.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()

