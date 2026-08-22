from pathlib import Path

path = Path("gui/settings_page.py")
text = path.read_text(encoding="utf-8")

if "from gui.discogs_settings_panel import DiscogsSettingsPanel" not in text:
    text = text.replace(
        "from PySide6.QtWidgets import (",
        "from gui.discogs_settings_panel import DiscogsSettingsPanel\n\nfrom PySide6.QtWidgets import (",
        1,
    )

old = 'self.stack.addWidget(self._placeholder_page("Discogs", "Discogs connection and enrichment preferences will live here."))'
new = 'self.stack.addWidget(DiscogsSettingsPanel())'

if old in text:
    text = text.replace(old, new, 1)
elif 'self.stack.addWidget(DiscogsSettingsPanel())' not in text:
    raise SystemExit("Discogs placeholder not found; no changes made.")

path.write_text(text, encoding="utf-8")
print("Discogs Settings gekoppeld.")
