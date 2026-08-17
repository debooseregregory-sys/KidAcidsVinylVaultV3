from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TARGET = BASE_DIR / "gui" / "main_window.py"

text = TARGET.read_text(encoding="utf-8-sig")

replacements = [
    (
        'from gui.release_library_page import ReleaseLibraryPage\n',
        'from gui.release_library_page import ReleaseLibraryPage\nfrom gui.release_board_page import ReleaseBoardPage\n'
    ),
    (
        '''        self.library_button = self.create_nav_button(\n            "▣",\n            "Release Library"\n        )\n\n        self.library_button.clicked.connect(\n            self.show_library\n        )\n\n        sidebar_layout.addWidget(\n            self.library_button\n        )\n''',
        '''        self.board_button = self.create_nav_button(\n            "▦",\n            "Release Board"\n        )\n\n        self.board_button.clicked.connect(\n            self.show_board\n        )\n\n        sidebar_layout.addWidget(\n            self.board_button\n        )\n\n        self.library_button = self.create_nav_button(\n            "▣",\n            "Release Library"\n        )\n\n        self.library_button.clicked.connect(\n            self.show_library\n        )\n\n        sidebar_layout.addWidget(\n            self.library_button\n        )\n'''
    ),
    (
        '''        # ====================================================\n        # RELEASE LIBRARY\n        # ====================================================\n\n        self.library_page = ReleaseLibraryPage()\n''',
        '''        # ====================================================\n        # RELEASE BOARD\n        # ====================================================\n\n        self.board_page = ReleaseBoardPage()\n\n        self.board_page.open_release.connect(\n            self.open_release\n        )\n\n        self.board_page.play_mp3.connect(\n            self.player_bar_play\n        )\n\n        self.pages.addWidget(\n            self.board_page\n        )\n\n        # ====================================================\n        # RELEASE LIBRARY\n        # ====================================================\n\n        self.library_page = ReleaseLibraryPage()\n'''
    ),
    (
        '''        buttons = [\n            self.home_button,\n            self.library_button,\n            self.discogs_button,\n        ]\n''',
        '''        buttons = [\n            self.home_button,\n            self.board_button,\n            self.library_button,\n            self.discogs_button,\n        ]\n'''
    ),
    (
        '''    # ========================================================\n    # RELEASE LIBRARY\n    # ========================================================\n\n    def show_library(\n''',
        '''    # ========================================================\n    # RELEASE BOARD\n    # ========================================================\n\n    def show_board(\n        self\n    ):\n\n        self.pages.setCurrentWidget(\n            self.board_page\n        )\n\n        self.page_title.setText(\n            "Release Board"\n        )\n\n        self.set_active_nav(\n            self.board_button\n        )\n\n    # ========================================================\n    # RELEASE LIBRARY\n    # ========================================================\n\n    def show_library(\n'''
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Blok verwacht 1 keer, gevonden {count}: {old[:80]!r}"
        )
    text = text.replace(old, new)

TARGET.write_text(text, encoding="utf-8")
print("RELEASE BOARD TOEGEVOEGD")
