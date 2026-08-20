# ============================================================
# ENABLE CD LIBRARY
# ============================================================
# Run once after pulling the CD-module branch.
# The script makes only targeted text changes and refuses to
# continue if the expected source structure is not present.

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "gui" / "main_window.py"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Veilige wijziging gestopt bij {label}: verwacht 1 match, gevonden {count}.")
    return text.replace(old, new, 1)


def main():
    text = MAIN.read_text(encoding="utf-8-sig")
    original = text

    text = replace_once(
        text,
        "from gui.release_showcase_page import ReleaseShowcasePage\n",
        "from gui.release_showcase_page import ReleaseShowcasePage\nfrom gui.cd_library_page import CDLibraryPage\n",
        "CD import",
    )

    text = replace_once(
        text,
        'self.cd_library_button.setEnabled(False)\n        self.cd_library_button.setToolTip("CD-module wordt toegevoegd zodra de CD-collectielijst is ingevoerd.")',
        'self.cd_library_button.clicked.connect(self.show_cd_library)',
        "CD Library button",
    )

    text = replace_once(
        text,
        '        self.mp3_showcase_page = MP3ShowcasePage()\n',
        '        self.mp3_showcase_page = MP3ShowcasePage()\n\n        # ====================================================\n        # CD LIBRARY\n        # ====================================================\n\n        self.cd_library_page = CDLibraryPage()\n        self.pages.addWidget(\n            self.cd_library_page\n        )\n',
        "CD page",
    )

    marker = "    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n"
    cd_method = '''    # ========================================================\n    # CD LIBRARY\n    # ========================================================\n\n    def show_cd_library(self):\n        self.pages.setCurrentWidget(self.cd_library_page)\n        self.page_title.setText("CD Library")\n        self.set_active_nav(self.cd_library_button)\n        if hasattr(self.cd_library_page, "load_releases"):\n            self.cd_library_page.load_releases()\n\n'''
    text = replace_once(text, marker, cd_method + marker, "CD navigation method")

    # Add CD Library to the active-navigation list.
    text = replace_once(
        text,
        "            self.home_button,            self.library_button,",
        "            self.home_button,            self.library_button,            self.cd_library_button,",
        "active navigation list",
    )

    if text == original:
        raise RuntimeError("Geen wijzigingen uitgevoerd.")

    MAIN.write_text(text, encoding="utf-8")
    print("CD Library is gekoppeld aan main_window.py")


if __name__ == "__main__":
    main()
