from pathlib import Path

p = Path('gui/main_window.py')
s = p.read_text(encoding='utf-8-sig')

# Add MP3 Showcase import when missing.
if 'from gui.mp3_showcase_page import MP3ShowcasePage' not in s:
    anchor = 'from gui.release_detail_page import ReleaseDetailPage\n'
    s = s.replace(anchor, anchor + 'from gui.mp3_showcase_page import MP3ShowcasePage\n', 1)

# Restore Dashboard button at the start of the library/navigation section.
if 'self.home_button = self.create_nav_button(' not in s:
    anchor = '''        # ====================================================\n        # RELEASE LIBRARY\n        # ====================================================\n'''
    block = '''        # ====================================================\n        # DASHBOARD\n        # ====================================================\n\n        self.home_button = self.create_nav_button(\n            "⌂",\n            "Dashboard"\n        )\n\n        self.home_button.clicked.connect(\n            self.show_home\n        )\n\n        sidebar_layout.addWidget(\n            self.home_button\n        )\n\n        # ====================================================\n        # VINYL\n        # ====================================================\n\n        vinyl_label = QLabel("VINYL")\n        vinyl_label.setObjectName("navigationLabel")\n        sidebar_layout.addSpacing(12)\n        sidebar_layout.addWidget(vinyl_label)\n\n'''
    s = s.replace(anchor, block + anchor, 1)

# Ensure MP3 Showcase page is constructed before the player section.
if 'self.mp3_showcase_page = MP3ShowcasePage()' not in s:
    anchor = '''        self.pages.addWidget(\n            self.discogs_page\n        )\n\n        right_layout.addWidget(\n'''
    block = '''        self.pages.addWidget(\n            self.discogs_page\n        )\n\n        # ====================================================\n        # MP3 SHOWCASE\n        # ====================================================\n\n        self.mp3_showcase_page = MP3ShowcasePage()\n        self.mp3_showcase_page.play_mp3.connect(\n            self.player_bar_play\n        )\n        self.pages.addWidget(\n            self.mp3_showcase_page\n        )\n\n        # ====================================================\n        # MP3 LIBRARY\n        # ====================================================\n\n        from gui.mp3_library_page import MP3LibraryPage\n        self.mp3_library_page = MP3LibraryPage()\n        self.mp3_library_page.play_mp3.connect(\n            self.player_bar_play\n        )\n        self.pages.addWidget(\n            self.mp3_library_page\n        )\n\n        right_layout.addWidget(\n'''
    s = s.replace(anchor, block, 1)

# Replace the broken/frozen old MP3/tool sidebar block with structured sections.
start = '        # ====================================================\n        # FUTURE NAVIGATION\n        # ====================================================\n'
end = '        sidebar_layout.addStretch()\n'
if start in s and end in s:
    a = s.index(start)
    b = s.index(end, a) + len(end)
    new_block = '''        # ====================================================\n        # VINYL TOOLS\n        # ====================================================\n\n        vinyl_tools_label = QLabel("VINYL TOOLS")\n        vinyl_tools_label.setObjectName("navigationLabel")\n        sidebar_layout.addWidget(vinyl_tools_label)\n\n        # Existing vinyl Discogs tool stays available here.\n        self.discogs_button = self.discogs_button if hasattr(self, "discogs_button") else self.create_nav_button("◈", "Discogs Import")\n\n        # ====================================================\n        # MP3\n        # ====================================================\n\n        mp3_label = QLabel("MP3")\n        mp3_label.setObjectName("navigationLabel")\n        sidebar_layout.addSpacing(18)\n        sidebar_layout.addWidget(mp3_label)\n\n        self.mp3_showcase_button = self.create_nav_button(\n            "♫",\n            "Showcase"\n        )\n        self.mp3_showcase_button.clicked.connect(\n            self.show_mp3_showcase\n        )\n        sidebar_layout.addWidget(\n            self.mp3_showcase_button\n        )\n\n        self.mp3_button = self.create_nav_button(\n            "▤",\n            "MP3 Library"\n        )\n        self.mp3_button.clicked.connect(\n            self.show_mp3_library\n        )\n        sidebar_layout.addWidget(\n            self.mp3_button\n        )\n\n        # ====================================================\n        # CD\n        # ====================================================\n\n        cd_label = QLabel("CD")\n        cd_label.setObjectName("navigationLabel")\n        sidebar_layout.addSpacing(18)\n        sidebar_layout.addWidget(cd_label)\n\n        self.cd_showcase_button = self.create_nav_button(\n            "●",\n            "Showcase"\n        )\n        self.cd_showcase_button.setEnabled(False)\n        sidebar_layout.addWidget(\n            self.cd_showcase_button\n        )\n\n        self.cd_library_button = self.create_nav_button(\n            "▤",\n            "CD Library"\n        )\n        self.cd_library_button.setEnabled(False)\n        sidebar_layout.addWidget(\n            self.cd_library_button\n        )\n\n        # ====================================================\n        # TOOLS\n        # ====================================================\n\n        tools_label = QLabel("TOOLS")\n        tools_label.setObjectName("navigationLabel")\n        sidebar_layout.addSpacing(18)\n        sidebar_layout.addWidget(tools_label)\n\n        # Discogs is the first technical tool.\n        sidebar_layout.addWidget(\n            self.discogs_button\n        )\n\n        self.settings_button = self.settings_button if hasattr(self, "settings_button") else self.create_nav_button("⚙", "Instellingen")\n        self.settings_button.setEnabled(False)\n        sidebar_layout.addWidget(\n            self.settings_button\n        )\n\n        sidebar_layout.addStretch()\n'''
    s = s[:a] + new_block + s[b:]

# Remove duplicate legacy additions if the new block already added discogs button after existing one.
# Keep only the first sidebar addWidget occurrence for discogs button in the navigation area by leaving runtime harmless if duplicate.

# Add page navigation methods before SHOW DISCOGS when missing.
if 'def show_mp3_showcase(' not in s:
    marker = '    # ========================================================\n    # DISCOGS\n    # ========================================================\n'
    methods = '''    # ========================================================\n    # MP3 SHOWCASE\n    # ========================================================\n\n    def show_mp3_showcase(self):\n        self.pages.setCurrentWidget(\n            self.mp3_showcase_page\n        )\n        self.page_title.setText(\n            "MP3 Showcase"\n        )\n        self.set_active_nav(\n            self.mp3_showcase_button\n        )\n\n    # ========================================================\n    # MP3 LIBRARY\n    # ========================================================\n\n    def show_mp3_library(self):\n        self.pages.setCurrentWidget(\n            self.mp3_library_page\n        )\n        self.page_title.setText(\n            "MP3 Library"\n        )\n        self.set_active_nav(\n            self.mp3_button\n        )\n\n'''
    s = s.replace(marker, methods + marker, 1)

# Extend active-nav list safely.
old = '''        buttons = [\n            self.home_button,\n            self.library_button,\n            self.discogs_button,\n        ]\n'''
new = '''        buttons = [\n            getattr(self, "home_button", None),\n            getattr(self, "library_button", None),\n            getattr(self, "discogs_button", None),\n            getattr(self, "mp3_showcase_button", None),\n            getattr(self, "mp3_button", None),\n            getattr(self, "cd_showcase_button", None),\n            getattr(self, "cd_library_button", None),\n            getattr(self, "settings_button", None),\n        ]\n'''
if old in s:
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8-sig')
print('Sidebar structure repaired and rebuilt.')
