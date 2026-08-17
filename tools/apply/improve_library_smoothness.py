from pathlib import Path

PATH = Path("gui/release_library_page.py")
text = PATH.read_text(encoding="utf-8-sig")

# Add QTimer.
old = "from PySide6.QtCore import Signal, Qt\n"
new = "from PySide6.QtCore import Signal, Qt, QTimer\n"
if "from PySide6.QtCore import Signal, Qt, QTimer" not in text:
    if text.count(old) != 1:
        raise RuntimeError("QtCore import patroon niet uniek")
    text = text.replace(old, new, 1)

# Add a short search debounce timer after status_filter.
old = '''        self.status_filter = "all"\n\n        self.build_ui()\n'''
new = '''        self.status_filter = "all"\n\n        self.search_timer = QTimer(self)\n        self.search_timer.setSingleShot(True)\n        self.search_timer.setInterval(140)\n        self.search_timer.timeout.connect(self.apply_pending_search)\n        self.pending_search_text = ""\n\n        self.build_ui()\n'''
if "self.search_timer = QTimer(self)" not in text:
    if text.count(old) != 1:
        raise RuntimeError("search timer marker niet uniek")
    text = text.replace(old, new, 1)

# Replace immediate search connection with debounced scheduling.
old = '''        self.search_input.textChanged.connect(\n            self.filter_releases\n        )\n'''
new = '''        self.search_input.textChanged.connect(\n            self.schedule_search\n        )\n'''
if "self.search_input.textChanged.connect(\n            self.schedule_search" not in text:
    if text.count(old) != 1:
        raise RuntimeError("search signal patroon niet gevonden")
    text = text.replace(old, new, 1)

# Add scheduling helpers before set_status_filter.
marker = '''    def set_status_filter(\n        self,\n        status\n    ):\n'''
methods = '''    def schedule_search(self, text):\n\n        self.pending_search_text = text\n        self.search_timer.start()\n\n    def apply_pending_search(self):\n\n        self.filter_releases(\n            self.pending_search_text\n        )\n\n    # ========================================================\n    # SET STATUS FILTER\n    # ========================================================\n\n'''
if "def schedule_search(self, text):" not in text:
    if text.count(marker) != 1:
        raise RuntimeError("status filter marker niet uniek")
    text = text.replace(marker, methods + marker, 1)

# Avoid repainting thousands of cells while rebuilding.
old = '''        self.table.setSortingEnabled(\n            False\n        )\n\n        self.table.setRowCount(\n            0\n        )\n'''
new = '''        self.table.setUpdatesEnabled(\n            False\n        )\n\n        self.table.setSortingEnabled(\n            False\n        )\n\n        self.table.setRowCount(\n            0\n        )\n'''
if "self.table.setUpdatesEnabled(\n            False" not in text:
    if text.count(old) != 1:
        raise RuntimeError("display refresh marker niet uniek")
    text = text.replace(old, new, 1)

old = '''        self.table.setSortingEnabled(\n            True\n        )\n\n        # ====================================================\n        # STATUS\n'''
new = '''        self.table.setSortingEnabled(\n            True\n        )\n\n        self.table.setUpdatesEnabled(\n            True\n        )\n\n        self.table.viewport().update()\n\n        # ====================================================\n        # STATUS\n'''
if "self.table.setUpdatesEnabled(\n            True" not in text:
    if text.count(old) != 1:
        raise RuntimeError("display restore marker niet uniek")
    text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8-sig")
print("RELEASE LIBRARY SMOOTHER GEMAAKT")
