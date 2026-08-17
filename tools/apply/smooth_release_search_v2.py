from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TARGET = BASE_DIR / "gui" / "release_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old_import = "from PySide6.QtCore import Signal, Qt\n"
new_import = "from PySide6.QtCore import Signal, Qt, QTimer\n"
if text.count(old_import) != 1:
    raise RuntimeError(f"Qt import verwacht 1 keer, gevonden {text.count(old_import)}")
text = text.replace(old_import, new_import)

old_init = '''        self.all_releases = []\n\n        self.status_filter = "all"\n'''
new_init = '''        self.all_releases = []\n        self._search_blob = []\n        self._search_timer = QTimer(self)\n        self._search_timer.setSingleShot(True)\n        self._search_timer.setInterval(220)\n        self._search_timer.timeout.connect(self._run_scheduled_search)\n\n        self.status_filter = "all"\n'''
if text.count(old_init) != 1:
    raise RuntimeError(f"init-blok verwacht 1 keer, gevonden {text.count(old_init)}")
text = text.replace(old_init, new_init)

old_connect = '''        self.search_input.textChanged.connect(\n            self.filter_releases\n        )\n'''
new_connect = '''        self.search_input.textChanged.connect(\n            self.schedule_filter_releases\n        )\n'''
if text.count(old_connect) != 1:
    raise RuntimeError(f"search-connect verwacht 1 keer, gevonden {text.count(old_connect)}")
text = text.replace(old_connect, new_connect)

old_loaded = '''        self.all_releases = rows\n\n        self.filter_releases(\n            self.search_input.text()\n        )\n'''
new_loaded = '''        self.all_releases = rows\n\n        self._search_blob = []\n        for row in rows:\n            values = [\n                row["id"],\n                row["artist"],\n                row["title"],\n                row["label"],\n                row["catalog"],\n                row["year"],\n                row["storage_code"],\n                row["discogs"],\n                row["genre"],\n            ]\n            self._search_blob.append(\n                " ".join(\n                    "" if value is None else str(value)\n                    for value in values\n                ).casefold()\n            )\n\n        self.filter_releases(\n            self.search_input.text()\n        )\n'''
if text.count(old_loaded) != 1:
    raise RuntimeError(f"load-blok verwacht 1 keer, gevonden {text.count(old_loaded)}")
text = text.replace(old_loaded, new_loaded)

old_filter = '''    def filter_releases(\n        self,\n        text\n    ):\n\n        search = (\n            text\n            .strip()\n            .lower()\n        )\n\n        filtered = []\n\n        for row in self.all_releases:\n\n            checked = False\n\n            try:\n                checked = int(\n                    row["checked"] or 0\n                ) == 1\n            except Exception:\n                checked = False\n\n            # ------------------------------------------------\n            # STATUS FILTER\n            # ------------------------------------------------\n\n            if self.status_filter == "todo" and checked:\n                continue\n\n            if self.status_filter == "checked" and not checked:\n                continue\n\n            # ------------------------------------------------\n            # TEXT SEARCH\n            # ------------------------------------------------\n\n            if search:\n\n                values = [\n                    row["id"],\n                    row["artist"],\n                    row["title"],\n                    row["label"],\n                    row["catalog"],\n                    row["year"],\n                    row["storage_code"],\n                    row["discogs"],\n                    row["genre"],\n                ]\n\n                combined = " ".join(\n                    "" if value is None\n                    else str(value)\n                    for value in values\n                ).lower()\n\n                if search not in combined:\n                    continue\n\n            filtered.append(\n                row\n            )\n\n        self.display_releases(\n            filtered\n        )\n'''
new_filter = '''    def schedule_filter_releases(\n        self,\n        text\n    ):\n\n        # De tekst in het veld blijft onmiddellijk responsief.\n        # De zware tabel-update wordt uitgesteld.\n        search = (text or "").strip()\n\n        self._search_timer.stop()\n\n        if len(search) < 2:\n            # Bij 0 of 1 teken geen dure tabel-herbouw.\n            # We laten de huidige tabel zichtbaar.\n            if not search:\n                self.filter_releases("")\n            return\n\n        self._search_timer.start()\n\n    def _run_scheduled_search(\n        self\n    ):\n\n        self.filter_releases(\n            self.search_input.text()\n        )\n\n    def filter_releases(\n        self,\n        text\n    ):\n\n        search = (\n            text\n            .strip()\n            .casefold()\n        )\n\n        # Eerste letter expres licht houden; vanaf 2 tekens zoeken.\n        if len(search) == 1:\n            return\n\n        filtered = []\n\n        for index, row in enumerate(self.all_releases):\n\n            checked = False\n\n            try:\n                checked = int(\n                    row["checked"] or 0\n                ) == 1\n            except Exception:\n                checked = False\n\n            if self.status_filter == "todo" and checked:\n                continue\n\n            if self.status_filter == "checked" and not checked:\n                continue\n\n            if search:\n                blob = (\n                    self._search_blob[index]\n                    if index < len(self._search_blob)\n                    else ""\n                )\n                if search not in blob:\n                    continue\n\n            filtered.append(row)\n\n        self.display_releases(\n            filtered\n        )\n'''
if text.count(old_filter) != 1:
    raise RuntimeError(f"filter-blok verwacht 1 keer, gevonden {text.count(old_filter)}")
text = text.replace(old_filter, new_filter)

TARGET.write_text(text, encoding="utf-8")
print("RELEASE SEARCH V2 TOGEPAST")
print("- eerste teken veroorzaakt geen zware tabel-refresh")
print("- zoeken begint vanaf 2 tekens")
print("- zoekvelden worden vooraf gecached")
print("- debounce: 220 ms")
