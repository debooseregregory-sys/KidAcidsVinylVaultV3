from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TARGET = BASE_DIR / "gui" / "main_window.py"

OLD = '''    def show_library(
        self
    ):

        self.library_page.load_releases()

        self.pages.setCurrentWidget(
            self.library_page
        )

        search_text = (
            self.library_page.search_input.text()
        )

        if search_text:
            self.library_page.filter_releases(
                search_text
            )

        self.page_title.setText(
            "Release Library"
        )

        self.set_active_nav(
            self.library_button
        )
'''

NEW = '''    def show_library(
        self
    ):

        # Navigeren moet direct zijn. De volledige database wordt
        # alleen opnieuw geladen via de knop VERWIEUW of na een
        # expliciete databasewijziging.
        self.pages.setCurrentWidget(
            self.library_page
        )

        search_text = (
            self.library_page.search_input.text()
        )

        if search_text:
            self.library_page.filter_releases(
                search_text
            )

        self.page_title.setText(
            "Release Library"
        )

        self.set_active_nav(
            self.library_button
        )
'''

text = TARGET.read_text(encoding="utf-8-sig")
count = text.count(OLD)
if count != 1:
    raise RuntimeError(
        f"show_library-blok verwacht 1 keer, gevonden {count}"
    )

TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
print("SIDEBAR NAVIGATIE VERSOEPELD")
print("show_library() laadt niet meer automatisch de volledige database opnieuw.")
