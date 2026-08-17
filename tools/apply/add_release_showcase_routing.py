from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "main_window.py"

text = TARGET.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# IMPORT
# ------------------------------------------------------------
import_anchor = "from gui.release_detail_page import ReleaseDetailPage\n"
import_line = "from gui.release_showcase_page import ReleaseShowcasePage\n"
if import_line not in text:
    if import_anchor not in text:
        raise RuntimeError("Import-anchor ReleaseDetailPage niet gevonden")
    text = text.replace(import_anchor, import_anchor + import_line, 1)

# ------------------------------------------------------------
# BOARD CONNECTION: OPEN -> SHOWCASE
# ------------------------------------------------------------
old_connection = "self.board_page.open_release.connect(\n            self.open_release\n        )"
new_connection = "self.board_page.open_release.connect(\n            self.show_showcase\n        )"
if old_connection in text:
    text = text.replace(old_connection, new_connection, 1)

# Alternative compact connection, in case the local file was formatted differently.
text = text.replace(
    "self.board_page.open_release.connect(self.open_release)",
    "self.board_page.open_release.connect(self.show_showcase)",
    1,
)

# ------------------------------------------------------------
# SHOWCASE PAGE
# ------------------------------------------------------------
if "self.showcase_page = ReleaseShowcasePage()" not in text:
    board_add = """        self.pages.addWidget(\n            self.board_page\n        )\n"""
    if board_add not in text:
        raise RuntimeError("Board page addWidget-blok niet gevonden")

    showcase_block = """        # ====================================================\n        # RELEASE SHOWCASE\n        # ====================================================\n\n        self.showcase_page = ReleaseShowcasePage()\n\n        self.showcase_page.back_requested.connect(\n            self.show_board\n        )\n\n        self.showcase_page.edit_requested.connect(\n            self.open_release\n        )\n\n        self.showcase_page.play_mp3.connect(\n            self.player_bar_play\n        )\n\n        self.pages.addWidget(\n            self.showcase_page\n        )\n\n"""
    text = text.replace(board_add, board_add + showcase_block, 1)

# ------------------------------------------------------------
# SHOWCASE METHOD
# ------------------------------------------------------------
if "def show_showcase(" not in text:
    marker = "    # ========================================================\n    # DISCOGS\n    # ========================================================\n"
    if marker not in text:
        raise RuntimeError("Method-marker voor DISCOGS niet gevonden")

    method = """    # ========================================================\n    # RELEASE SHOWCASE\n    # ========================================================\n\n    def show_showcase(\n        self,\n        release_id\n    ):\n\n        self.showcase_page.load_release(\n            release_id\n        )\n\n        self.pages.setCurrentWidget(\n            self.showcase_page\n        )\n\n        self.page_title.setText(\n            \"Release\"\n        )\n\n        self.set_active_nav(\n            self.board_button\n        )\n\n"""
    text = text.replace(marker, method + marker, 1)

TARGET.write_text(text, encoding="utf-8")
print("RELEASE BOARD -> SHOWCASE -> EDITOR ROUTING TOEGEVOEGD")
print("Board openen toont nu eerst de alleen-lezen Showcase.")
print("Vanuit Showcase gaat BEWERKEN naar de bestaande Editor.")
