from pathlib import Path

path = Path("gui/main_window.py")
text = path.read_text(encoding="utf-8")

required_import = "from gui.settings_page import SettingsPage\n"
if required_import not in text:
    marker = "from gui.mp3_showcase_playback_bridge import install_mp3_showcase_playback_bridge\n"
    if marker not in text:
        raise SystemExit("Import marker not found; main_window.py was not modified.")
    text = text.replace(marker, marker + required_import, 1)

old_nav = '''        self.settings_button = self.create_nav_button("⚙", "Instellingen")
        self.settings_button.setEnabled(False)
        self.settings_button.setToolTip("Instellingen worden later toegevoegd.")
        sidebar_layout.addWidget(self.settings_button)
'''
new_nav = '''        self.settings_button = self.create_nav_button("⚙", "Settings")
        self.settings_button.clicked.connect(self.show_settings)
        sidebar_layout.addWidget(self.settings_button)
'''
if old_nav in text:
    text = text.replace(old_nav, new_nav, 1)
elif 'self.settings_button.clicked.connect(self.show_settings)' not in text:
    raise SystemExit("Settings navigation block not found; main_window.py was not modified.")

page_marker = '''        self.pages.addWidget(
            self.cd_library_page
        )
        install_mp3_showcase_playback_bridge()
'''
page_insert = '''        self.pages.addWidget(
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
'''
if page_marker in text:
    text = text.replace(page_marker, page_insert, 1)
elif 'self.settings_page = SettingsPage()' not in text:
    raise SystemExit("Page insertion marker not found; main_window.py was not modified.")

method_marker = '''    # ========================================================
    # CD LIBRARY
    # ========================================================

    def show_cd_library(self):
'''
method_insert = '''    # ========================================================
    # SETTINGS
    # ========================================================

    def show_settings(self):
        self.pages.setCurrentWidget(self.settings_page)
        self.page_title.setText("Settings")
        self.set_active_nav(self.settings_button)

    # ========================================================
    # CD LIBRARY
    # ========================================================

    def show_cd_library(self):
'''
if method_marker in text:
    text = text.replace(method_marker, method_insert, 1)
elif 'def show_settings(self):' not in text:
    raise SystemExit("Method insertion marker not found; main_window.py was not modified.")

# Add the settings button to active-navigation handling.
old_buttons = '''            self.home_button,            self.library_button,
            self.vinyl_showcase_button,
            self.discogs_button,
'''
new_buttons = '''            self.home_button,            self.library_button,
            self.vinyl_showcase_button,
            self.discogs_button,
            self.settings_button,
'''
if old_buttons in text:
    text = text.replace(old_buttons, new_buttons, 1)

path.write_text(text, encoding="utf-8", newline="\n")
print("MusicVault Settings integrated successfully.")
