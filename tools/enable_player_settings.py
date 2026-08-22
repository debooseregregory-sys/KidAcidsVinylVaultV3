from pathlib import Path

path = Path("gui/settings_page.py")
text = path.read_text(encoding="utf-8")

old = '        self.stack.addWidget(self._placeholder_page("Player", "Playback behaviour, volume, transitions and visualizer preferences will live here."))'
new = '        self.stack.addWidget(self._player_page())'

if old not in text:
    raise SystemExit("Player placeholder not found; settings_page.py may already be integrated.")

marker = '    def _placeholder_page(self, title, description):\n'
method = '''    def _player_page(self):\n        from gui.player_settings_panel import PlayerSettingsPanel\n        return PlayerSettingsPanel()\n\n'''

if marker not in text:
    raise SystemExit("Settings placeholder method marker not found.")

text = text.replace(old, new, 1)
text = text.replace(marker, method + marker, 1)
path.write_text(text, encoding="utf-8")
print("Player Settings integrated into MusicVault Settings.")
