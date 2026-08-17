from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "gui" / "main_window.py"

text = PATH.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

if "from gui.mp3_library_page import MP3LibraryPage" not in text:
    text = text.replace(
        "from gui.player_bar import PlayerBar\n",
        "from gui.player_bar import PlayerBar\nfrom gui.mp3_library_page import MP3LibraryPage\nfrom gui.mp3_showcase_page import MP3ShowcasePage\n",
        1,
    )

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------

start = text.find("        # ====================================================\n        # NAVIGATION TITLE")
end = text.find("        # ====================================================\n        # SIDEBAR FOOTER", start)

if start == -1 or end == -1:
    raise SystemExit("Sidebar navigation markers not found; no changes made.")

sidebar = '''        # ====================================================
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
        self.cd_library_button.setEnabled(False)
        self.cd_library_button.setToolTip("CD-module wordt toegevoegd zodra de CD-collectielijst is ingevoerd.")
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

        self.settings_button = self.create_nav_button("⚙", "Instellingen")
        self.settings_button.setEnabled(False)
        self.settings_button.setToolTip("Instellingen worden later toegevoegd.")
        sidebar_layout.addWidget(self.settings_button)

'''

text = text[:start] + sidebar + text[end:]

# ------------------------------------------------------------
# PAGE CREATION
# ------------------------------------------------------------

marker = "        self.pages.addWidget(\n            self.discogs_page\n        )\n"

if "self.mp3_showcase_page = MP3ShowcasePage()" not in text:
    pages = marker + '''
        # ====================================================
        # MP3 SHOWCASE
        # ====================================================

        self.mp3_showcase_page = MP3ShowcasePage()
        self.mp3_showcase_page.play_mp3.connect(self.player_bar_play)
        self.pages.addWidget(self.mp3_showcase_page)

        # ====================================================
        # MP3 LIBRARY
        # ====================================================

        self.mp3_library_page = MP3LibraryPage()
        self.mp3_library_page.play_mp3.connect(self.player_bar_play)
        self.pages.addWidget(self.mp3_library_page)
'''
    text = text.replace(marker, pages, 1)

# ------------------------------------------------------------
# ACTIVE NAVIGATION
# ------------------------------------------------------------

old_buttons = '''        buttons = [
            self.home_button,
            self.library_button,
            self.discogs_button,
        ]
'''

new_buttons = '''        buttons = [
            self.home_button,
            self.vinyl_showcase_button,
            self.library_button,
            self.mp3_showcase_button,
            self.mp3_button,
            self.cd_showcase_button,
            self.cd_library_button,
            self.discogs_button,
            self.settings_button,
        ]
'''

if old_buttons in text:
    text = text.replace(old_buttons, new_buttons, 1)

# ------------------------------------------------------------
# NAVIGATION METHODS
# ------------------------------------------------------------

marker = "    # ========================================================\n    # HOME\n"

methods = '''    # ========================================================
    # VINYL SHOWCASE
    # ========================================================

    def show_vinyl_showcase(self):
        # Reuse the existing Release Library as the visual Vinyl entry point
        # until a dedicated Vinyl Showcase page is promoted here.
        self.show_library()

    # ========================================================
    # MP3 SHOWCASE
    # ========================================================

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

'''

if "def show_mp3_showcase(self):" not in text:
    text = text.replace(marker, methods + marker, 1)

# ------------------------------------------------------------
# COLLECTION LABELS STYLE
# ------------------------------------------------------------

needle = '''            QLabel#navigationLabel {
                background: transparent;
                color: #666672;
                font-size: 10px;
                font-weight: bold;
                padding-left: 12px;
                letter-spacing: 1.5px;
            }
'''

addition = needle + '''
            QLabel#collectionSectionLabel {
                background: transparent;
                color: #d84b91;
                font-size: 10px;
                font-weight: 900;
                padding-left: 12px;
                margin-top: 2px;
                letter-spacing: 1.8px;
            }
'''

if "QLabel#collectionSectionLabel" not in text and needle in text:
    text = text.replace(needle, addition, 1)

PATH.write_text(text, encoding="utf-8-sig")
print("Sidebar structure updated: VINYL / MP3 / CD / TOOLS")
