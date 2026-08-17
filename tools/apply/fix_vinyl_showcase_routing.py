from pathlib import Path
import re

p = Path("gui/main_window.py")
s = p.read_text(encoding="utf-8-sig")

# 1. Import showcase page.
if "from gui.release_showcase_page import ReleaseShowcasePage" not in s:
    anchor = "from gui.release_library_page import ReleaseLibraryPage\n"
    if anchor not in s:
        raise SystemExit("ReleaseLibraryPage import anchor niet gevonden")
    s = s.replace(anchor, anchor + "from gui.release_showcase_page import ReleaseShowcasePage\n", 1)

# 2. Create showcase page after library page.
if "self.showcase_page = ReleaseShowcasePage()" not in s:
    anchor = '''        self.library_page = ReleaseLibraryPage()\n\n        self.library_page.release_selected.connect(\n            self.open_release\n        )\n\n        self.pages.addWidget(\n            self.library_page\n        )\n'''
    block = '''        self.library_page = ReleaseLibraryPage()\n\n        self.library_page.release_selected.connect(\n            self.open_release\n        )\n\n        self.pages.addWidget(\n            self.library_page\n        )\n\n        # ====================================================\n        # VINYL SHOWCASE\n        # ====================================================\n\n        self.showcase_page = ReleaseShowcasePage()\n\n        self.showcase_page.back_requested.connect(\n            self.show_library\n        )\n\n        self.showcase_page.edit_requested.connect(\n            self.open_release_editor\n        )\n\n        self.showcase_page.play_mp3.connect(\n            self.player_bar_play\n        )\n\n        self.pages.addWidget(\n            self.showcase_page\n        )\n'''
    if anchor not in s:
        raise SystemExit("Release Library page block niet gevonden")
    s = s.replace(anchor, block, 1)

# 3. Add showcase button if missing. Insert before the next collection/tool section.
if "self.vinyl_showcase_button = self.create_nav_button(" not in s:
    anchor = '''        self.library_button.clicked.connect(\n            self.show_library\n        )\n\n        sidebar_layout.addWidget(\n            self.library_button\n        )\n'''
    block = '''        self.library_button.clicked.connect(\n            self.show_library\n        )\n\n        sidebar_layout.addWidget(\n            self.library_button\n        )\n\n        self.vinyl_showcase_button = self.create_nav_button(\n            "◉",\n            "Vinyl Showcase"\n        )\n\n        self.vinyl_showcase_button.clicked.connect(\n            self.show_vinyl_showcase\n        )\n\n        sidebar_layout.addWidget(\n            self.vinyl_showcase_button\n        )\n'''
    if anchor not in s:
        raise SystemExit("library button block niet gevonden")
    s = s.replace(anchor, block, 1)

# 4. Add methods before DISCOGS section.
if "def show_vinyl_showcase(" not in s:
    marker = "    # ========================================================\n    # DISCOGS\n    # ========================================================\n"
    methods = '''    # ========================================================\n    # VINYL SHOWCASE\n    # ========================================================\n\n    def show_vinyl_showcase(\n        self,\n        release_id=None\n    ):\n\n        if release_id is None:\n            # Use the currently selected/visible release when available.\n            try:\n                ids = self.library_page.visible_release_ids()\n                if ids:\n                    release_id = ids[0]\n            except Exception:\n                release_id = None\n\n        if release_id is None:\n            self.page_title.setText(\n                "Vinyl Showcase"\n            )\n            self.pages.setCurrentWidget(\n                self.library_page\n            )\n            self.set_active_nav(\n                self.vinyl_showcase_button\n            )\n            return\n\n        self.showcase_page.load_release(\n            release_id\n        )\n\n        self.pages.setCurrentWidget(\n            self.showcase_page\n        )\n\n        self.page_title.setText(\n            "Vinyl Showcase"\n        )\n\n        self.set_active_nav(\n            self.vinyl_showcase_button\n        )\n\n    def open_release_editor(\n        self,\n        release_id\n    ):\n\n        self.detail_page.load_release(\n            release_id\n        )\n\n        self.pages.setCurrentWidget(\n            self.detail_page\n        )\n\n        self.page_title.setText(\n            "Release Editor"\n        )\n\n        self.set_active_nav(\n            self.library_button\n        )\n\n'''
    if marker not in s:
        raise SystemExit("Discogs marker niet gevonden")
    s = s.replace(marker, methods + marker, 1)

# 5. Update open_release so board/library selection opens showcase first.
pattern = re.compile(
    r"    def open_release\(\n        self,\n        release_id,\n        release_ids=None\n    \):\n.*?        self.set_active_nav\(\n            self\.library_button\n        \)\n", re.S,
)
if not pattern.search(s):
    raise SystemExit("open_release functie niet gevonden")

new_open = '''    def open_release(\n        self,\n        release_id,\n        release_ids=None\n    ):\n\n        self.showcase_page.load_release(\n            release_id\n        )\n\n        self.pages.setCurrentWidget(\n            self.showcase_page\n        )\n\n        self.page_title.setText(\n            "Vinyl Showcase"\n        )\n\n        self.set_active_nav(\n            self.vinyl_showcase_button\n        )\n'''
s = pattern.sub(new_open, s, count=1)

# 6. Ensure navigation knows about showcase button.
if "self.vinyl_showcase_button," not in s:
    anchor = "            self.library_button,\n"
    if anchor not in s:
        raise SystemExit("set_active_nav anchor niet gevonden")
    s = s.replace(anchor, anchor + "            self.vinyl_showcase_button,\n", 1)

p.write_text(s, encoding="utf-8-sig")
print("VINYL SHOWCASE ROUTING TOEGEVOEGD")
