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
        raise RuntimeError(
            f"Veilige wijziging gestopt bij {label}: verwacht 1 match, gevonden {count}."
        )
    return text.replace(old, new, 1)


def main():
    text = MAIN.read_text(encoding="utf-8-sig")
    original = text

    if "from gui.cd_library_page import CDLibraryPage" not in text:
        text = replace_once(
            text,
            "from gui.release_showcase_page import ReleaseShowcasePage\n",
            "from gui.release_showcase_page import ReleaseShowcasePage\nfrom gui.cd_library_page import CDLibraryPage\n",
            "CD import",
        )

    disabled = 'self.cd_library_button.setEnabled(False)\n        self.cd_library_button.setToolTip("CD-module wordt toegevoegd zodra de CD-collectielijst is ingevoerd.")'
    connected = 'self.cd_library_button.clicked.connect(self.show_cd_library)'
    if connected not in text:
        text = replace_once(text, disabled, connected, "CD Library button")

    page_block = '''        # ====================================================
        # CD LIBRARY
        # ====================================================

        self.cd_library_page = CDLibraryPage()
        self.pages.addWidget(
            self.cd_library_page
        )
'''
    if "self.cd_library_page = CDLibraryPage()" not in text:
        text = replace_once(
            text,
            '        self.mp3_showcase_page = MP3ShowcasePage()\n',
            '        self.mp3_showcase_page = MP3ShowcasePage()\n\n' + page_block,
            "CD page",
        )

    if "def show_cd_library(self):" not in text:
        marker = "    # ========================================================\n    # CREATE NAV BUTTON\n    # ========================================================\n"
        cd_method = '''    # ========================================================
    # CD LIBRARY
    # ========================================================

    def show_cd_library(self):
        self.pages.setCurrentWidget(self.cd_library_page)
        self.page_title.setText("CD Library")
        self.set_active_nav(self.cd_library_button)
        if hasattr(self.cd_library_page, "load_releases"):
            self.cd_library_page.load_releases()

'''
        text = replace_once(text, marker, cd_method + marker, "CD navigation method")

    # Active highlighting is optional; navigation itself must never depend on it.
    if "self.cd_library_button" not in text:
        raise RuntimeError("CD Library button kon niet worden gevonden.")

    if text == original:
        print("CD Library was al gekoppeld.")
        return

    MAIN.write_text(text, encoding="utf-8")
    print("CD Library is gekoppeld aan main_window.py")


if __name__ == "__main__":
    main()
