from pathlib import Path

TARGET = Path("gui/release_library_page.py")

source = TARGET.read_text(encoding="utf-8-sig")

# Add QTimer import.
source = source.replace(
    "from PySide6.QtCore import Signal, Qt",
    "from PySide6.QtCore import Signal, Qt, QTimer",
    1,
)

# Add debounce timer after status_filter initialization.
old = '''        self.status_filter = "all"\n\n        self.build_ui()'''
new = '''        self.status_filter = "all"\n\n        self.search_timer = QTimer(self)\n        self.search_timer.setSingleShot(True)\n        self.search_timer.setInterval(180)\n        self.search_timer.timeout.connect(self._run_pending_search)\n        self._pending_search_text = ""\n\n        self.build_ui()'''
if old not in source:
    raise SystemExit("INIT marker niet gevonden")
source = source.replace(old, new, 1)

# Replace direct textChanged connection.
old = '''        self.search_input.textChanged.connect(\n            self.filter_releases\n        )'''
new = '''        self.search_input.textChanged.connect(\n            self._schedule_search\n        )'''
if old not in source:
    raise SystemExit("SEARCH connection niet gevonden")
source = source.replace(old, new, 1)

# Insert debounce methods immediately before FILTER RELEASES.
marker = '''    # ========================================================\n    # FILTER RELEASES\n    # ========================================================\n\n    def filter_releases(\n'''
insert = '''    # ========================================================\n    # SMOOTH SEARCH\n    # ========================================================\n\n    def _schedule_search(\n        self,\n        text\n    ):\n\n        self._pending_search_text = text\n\n        self.search_timer.start()\n\n    def _run_pending_search(\n        self\n    ):\n\n        self.filter_releases(\n            self._pending_search_text\n        )\n\n    # ========================================================\n    # FILTER RELEASES\n    # ========================================================\n\n    def filter_releases(\n'''
if marker not in source:
    raise SystemExit("FILTER marker niet gevonden")
source = source.replace(marker, insert, 1)

TARGET.write_text(source, encoding="utf-8-sig")
print("Release Library zoekbalk is soepeler gemaakt (180 ms debounce).")
