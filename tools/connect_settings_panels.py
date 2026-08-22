from pathlib import Path

path = Path("gui/settings_page.py")
text = path.read_text(encoding="utf-8")

# Add imports once.
if "from gui.music_library_settings_panel import MusicLibrarySettingsPanel" not in text:
    marker = "from gui.discogs_settings_panel import DiscogsSettingsPanel\n"
    if marker in text:
        text = text.replace(
            marker,
            marker + "from gui.music_library_settings_panel import MusicLibrarySettingsPanel\n"
                     "from gui.database_settings_panel import DatabaseSettingsPanel\n",
            1,
        )
    else:
        marker = "from PySide6.QtWidgets import (\n"
        text = text.replace(
            marker,
            "from gui.music_library_settings_panel import MusicLibrarySettingsPanel\n"
            "from gui.database_settings_panel import DatabaseSettingsPanel\n\n" + marker,
            1,
        )
elif "from gui.database_settings_panel import DatabaseSettingsPanel" not in text:
    text = text.replace(
        "from gui.music_library_settings_panel import MusicLibrarySettingsPanel\n",
        "from gui.music_library_settings_panel import MusicLibrarySettingsPanel\n"
        "from gui.database_settings_panel import DatabaseSettingsPanel\n",
        1,
    )

# Replace only the two placeholder pages. Leave all other Settings pages untouched.
old_music = 'self.stack.addWidget(self._placeholder_page("Music Library", "MP3 scanning, matching behaviour and library presentation will live here."))'
old_discogs = 'self.stack.addWidget(self._placeholder_page("Discogs", "Discogs connection and enrichment preferences will live here."))'
old_database = 'self.stack.addWidget(self._placeholder_page("Database", "Safe database information and backup tools will live here."))'

if old_music in text:
    text = text.replace(
        old_music,
        'self.music_library_settings_panel = MusicLibrarySettingsPanel()\n'
        '        self.stack.addWidget(self.music_library_settings_panel)',
        1,
    )

# Keep an existing real Discogs panel if the local file already has one.
if old_discogs in text:
    text = text.replace(
        old_discogs,
        'self.discogs_settings_panel = DiscogsSettingsPanel()\n'
        '        self.stack.addWidget(self.discogs_settings_panel)',
        1,
    )

if old_database in text:
    text = text.replace(
        old_database,
        'self.database_settings_panel = DatabaseSettingsPanel()\n'
        '        self.stack.addWidget(self.database_settings_panel)',
        1,
    )

# If the local file already contains a direct Discogs panel, do not duplicate it.
if "self.discogs_settings_panel = DiscogsSettingsPanel()" not in text and "self.stack.addWidget(DiscogsSettingsPanel())" in text:
    text = text.replace(
        "self.stack.addWidget(DiscogsSettingsPanel())",
        'self.discogs_settings_panel = DiscogsSettingsPanel()\n'
        '        self.stack.addWidget(self.discogs_settings_panel)',
        1,
    )

path.write_text(text, encoding="utf-8")
print("Settings panels connected: Music Library + Discogs + Database")
