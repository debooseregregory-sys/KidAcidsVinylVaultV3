from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / 'gui' / 'main_window.py'

text = TARGET.read_text(encoding='utf-8-sig')

# Import
if 'from gui.mp3_showcase_page import MP3ShowcasePage' not in text:
    if 'from gui.mp3_library_page import MP3LibraryPage' in text:
        text = text.replace(
            'from gui.mp3_library_page import MP3LibraryPage',
            'from gui.mp3_library_page import MP3LibraryPage\nfrom gui.mp3_showcase_page import MP3ShowcasePage',
            1,
        )
    elif 'from gui.player import MP3Player' in text:
        text = text.replace(
            'from gui.player import MP3Player',
            'from gui.mp3_showcase_page import MP3ShowcasePage\nfrom gui.player import MP3Player',
            1,
        )

# Sidebar: enable existing MP3 button and add showcase button.
if 'self.mp3_showcase_button' not in text:
    old = '''        self.mp3_button = self.create_nav_button(\n            "♫",\n            "MP3 Library"\n        )\n\n        self.mp3_button.setEnabled(\n            False\n        )\n\n        sidebar_layout.addWidget(\n            self.mp3_button\n        )\n'''
    new = '''        self.mp3_button = self.create_nav_button(\n            "♫",\n            "MP3 Library"\n        )\n\n        if hasattr(self, "show_mp3_library"):\n            self.mp3_button.setEnabled(True)\n            self.mp3_button.clicked.connect(self.show_mp3_library)\n\n        sidebar_layout.addWidget(\n            self.mp3_button\n        )\n\n        self.mp3_showcase_button = self.create_nav_button(\n            "▶",\n            "MP3 Showcase"\n        )\n\n        self.mp3_showcase_button.clicked.connect(\n            self.show_mp3_showcase\n        )\n\n        sidebar_layout.addWidget(\n            self.mp3_showcase_button\n        )\n'''
    if old in text:
        text = text.replace(old, new, 1)
    else:
        # Local versions may already have MP3 Library but with slightly different spacing.
        marker = '        self.settings_button = self.create_nav_button('
        block = '''        self.mp3_showcase_button = self.create_nav_button(\n            "▶",\n            "MP3 Showcase"\n        )\n\n        self.mp3_showcase_button.clicked.connect(\n            self.show_mp3_showcase\n        )\n\n        sidebar_layout.addWidget(\n            self.mp3_showcase_button\n        )\n\n'''
        if marker in text:
            text = text.replace(marker, block + marker, 1)

# Page stack.
if 'self.mp3_showcase_page = MP3ShowcasePage()' not in text:
    marker = '        right_layout.addWidget(\n            self.pages,\n            1\n        )'
    block = '''        # ====================================================\n        # MP3 SHOWCASE\n        # ====================================================\n\n        self.mp3_showcase_page = MP3ShowcasePage()\n\n        self.mp3_showcase_page.play_mp3.connect(\n            self.player_bar_play\n        )\n\n        self.pages.addWidget(\n            self.mp3_showcase_page\n        )\n\n'''
    if marker in text:
        text = text.replace(marker, block + marker, 1)

# Navigation methods.
if 'def show_mp3_showcase(' not in text:
    marker = '    # ========================================================\n    # PLAY MP3\n    # ========================================================\n'
    block = '''    # ========================================================\n    # MP3 SHOWCASE\n    # ========================================================\n\n    def show_mp3_showcase(\n        self\n    ):\n\n        self.pages.setCurrentWidget(\n            self.mp3_showcase_page\n        )\n\n        self.page_title.setText(\n            "MP3 Showcase"\n        )\n\n        if hasattr(self, "mp3_showcase_button"):\n            self.set_active_nav(\n                self.mp3_showcase_button\n            )\n\n    # ========================================================\n    # PLAY MP3\n    # ========================================================\n'''
    if marker in text:
        text = text.replace(marker, block, 1)

# Include Showcase in active-nav list.
if 'self.mp3_showcase_button,' not in text:
    old = '''            self.home_button,\n            self.library_button,\n            self.discogs_button,\n'''
    new = '''            self.home_button,\n            self.library_button,\n            self.discogs_button,\n            *(\n                [self.mp3_button, self.mp3_showcase_button]\n                if hasattr(self, "mp3_showcase_button")\n                else []\n            ),\n'''
    if old in text:
        text = text.replace(old, new, 1)

TARGET.write_text(text, encoding='utf-8-sig')
print('MP3 Showcase koppeling toegepast.')
