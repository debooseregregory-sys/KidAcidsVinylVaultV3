# ============================================================
# KID ACID'S VINYLVAULT V3
# MAIN WINDOW
#
# PROFESSIONAL DESKTOP INTERFACE
# ============================================================

import sys

from PySide6.QtCore import Qt
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
from gui.release_detail_page import ReleaseDetailPage
from gui.player import MP3Player
from gui.player_bar import PlayerBar


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
            "Kid Acid's VinylVault V3"
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
            "VINYLVAULT"
        )

        brand_title.setObjectName(
            "brandTitle"
        )

        brand_layout.addWidget(
            brand_title
        )

        brand_version = QLabel(
            "V3  •  DESKTOP COLLECTION"
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
        # NAVIGATION TITLE
        # ====================================================

        navigation_label = QLabel(
            "LIBRARY"
        )

        navigation_label.setObjectName(
            "navigationLabel"
        )

        sidebar_layout.addWidget(
            navigation_label
        )

        sidebar_layout.addSpacing(
            4
        )

        # ====================================================
        # HOME
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
        # RELEASE LIBRARY
        # ====================================================

        self.library_button = self.create_nav_button(
            "▣",
            "Release Library"
        )

        self.library_button.clicked.connect(
            self.show_library
        )

        sidebar_layout.addWidget(
            self.library_button
        )

        # ====================================================
        # DISCOGS
        # ====================================================

        self.discogs_button = self.create_nav_button(
            "◈",
            "Discogs Import"
        )

        self.discogs_button.clicked.connect(
            self.show_discogs
        )

        sidebar_layout.addWidget(
            self.discogs_button
        )

        # ====================================================
        # FUTURE NAVIGATION
        # ====================================================

        tools_label = QLabel(
            "TOOLS"
        )

        tools_label.setObjectName(
            "navigationLabel"
        )

        sidebar_layout.addSpacing(
            22
        )

        sidebar_layout.addWidget(
            tools_label
        )

        self.mp3_button = self.create_nav_button(
            "♫",
            "MP3 Library"
        )

        self.mp3_button.setEnabled(
            False
        )

        sidebar_layout.addWidget(
            self.mp3_button
        )

        self.settings_button = self.create_nav_button(
            "⚙",
            "Instellingen"
        )

        self.settings_button.setEnabled(
            False
        )

        sidebar_layout.addWidget(
            self.settings_button
        )

        sidebar_layout.addStretch()

        # ====================================================
        # SIDEBAR FOOTER
        # ====================================================

        footer = QLabel(
            "VINYL ONLY  •  KID ACID"
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
            "VINYL COLLECTION"
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

        self.discogs_page.import_finished.connect(
            self.refresh_after_import
        )

        self.pages.addWidget(
            self.discogs_page
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
            "VinylVault database actief"
        )

        status_text.setObjectName(
            "statusTitle"
        )

        status_layout.addWidget(
            status_text
        )

        status_layout.addStretch()

        database_text = QLabel(
            "Lokale collectie • Database verbonden"
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

        return page

    # ========================================================
    # ACTIVE NAVIGATION
    # ========================================================

    def set_active_nav(
        self,
        button
    ):

        buttons = [
            self.home_button,
            self.library_button,
            self.discogs_button,
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
    # RELEASE LIBRARY
    # ========================================================

    def show_library(
        self
    ):

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

        self.detail_page.set_navigation_ids(
            release_ids
        )

        self.detail_page.load_release(
            release_id
        )

        self.pages.setCurrentWidget(
            self.detail_page
        )

        self.page_title.setText(
            "Release Detail"
        )

        self.set_active_nav(
            self.library_button
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
            "VinylVault: database gewijzigd."
        )

        self.library_page.load_releases()

    # ========================================================
    # STYLE
    # ========================================================

    def apply_style(
        self
    ):

        self.setStyleSheet(
            """
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
                color: #a8a8b3;
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
                color: inherit;
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
            """
        )


# ============================================================
# START
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Kid Acid's VinylVault V3"
    )

    app.setApplicationDisplayName(
        "Kid Acid's VinylVault V3"
    )

    app.setStyle(
        "Fusion"
    )

    window = VinylVaultWindow()

    window.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()