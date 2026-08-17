from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "main_window.py"

text = TARGET.read_text(encoding="utf-8-sig")

# Import
if "from gui.mp3_library_page import MP3LibraryPage" not in text:
    anchor = "from gui.player import MP3Player\n"
    if anchor not in text:
        raise RuntimeError("Import-anchor MP3Player niet gevonden")
    text = text.replace(anchor, anchor + "from gui.mp3_library_page import MP3LibraryPage\n", 1)

# Enable sidebar button and connect it.
old = '''        self.mp3_button = self.create_nav_button(\n            "♫",\n            "MP3 Library"\n        )\n\n        self.mp3_button.setEnabled(\n            False\n        )\n\n        sidebar_layout.addWidget(\n            self.mp3_button\n        )\n'''
new = '''        self.mp3_button = self.create_nav_button(\n            "♫",\n            "MP3 Library"\n        )\n\n        self.mp3_button.clicked.connect(\n            self.show_mp3_library\n        )\n\n        sidebar_layout.addWidget(\n            self.mp3_button\n        )\n'''
if old in text:
    text = text.replace(old, new, 1)
elif "self.mp3_button.clicked.connect(" not in text:
    raise RuntimeError("MP3 sidebar-blok niet gevonden")

# Create page after Discogs page creation, if not already present.
if "self.mp3_library_page = MP3LibraryPage()" not in text:
    anchor = '''        self.discogs_page = DiscogsImportPage()\n\n'''
    if anchor not in text:
        raise RuntimeError("Discogs page creation anchor niet gevonden")
    block = '''        # ====================================================\n        # MP3 LIBRARY\n        # ====================================================\n\n        self.mp3_library_page = MP3LibraryPage()\n\n        self.mp3_library_page.play_mp3.connect(\n            self.player_bar_play\n        )\n\n        self.pages.addWidget(\n            self.mp3_library_page\n        )\n\n'''
    text = text.replace(anchor, anchor + block, 1)

# Add navigation method before show_discogs.
if "def show_mp3_library(" not in text:
    marker = "    # ========================================================\n    # DISCOGS\n    # ========================================================\n"
    if marker not in text:
        raise RuntimeError("show_discogs marker niet gevonden")
    method = '''    # ========================================================\n    # MP3 LIBRARY\n    # ========================================================\n\n    def show_mp3_library(self):\n\n        self.mp3_library_page.load_data()\n\n        self.pages.setCurrentWidget(\n            self.mp3_library_page\n        )\n\n        self.page_title.setText(\n            "MP3 Library"\n        )\n\n        self.set_active_nav(\n            self.mp3_button\n        )\n\n'''
    text = text.replace(marker, method + marker, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 LIBRARY GEKOPPELD AAN SIDEBAR EN PLAYER")
