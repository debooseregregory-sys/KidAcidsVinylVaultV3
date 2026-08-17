from pathlib import Path

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

# Add QDesktopServices/QUrl imports if missing.
if "QDesktopServices" not in text:
    text = text.replace(
        "from PySide6.QtCore import Qt, QThread, Signal",
        "from PySide6.QtCore import Qt, QThread, Signal, QUrl\nfrom PySide6.QtGui import QDesktopServices"
    )

# Add double-click connection.
needle = "self.list.itemSelectionChanged.connect(self.refresh_button_state)"
if needle in text and "self.list.itemDoubleClicked.connect(self.play_double_clicked)" not in text:
    text = text.replace(
        needle,
        needle + "\n        self.list.itemDoubleClicked.connect(self.play_double_clicked)"
    )

# Add playback method before selected_group_keys.
marker = "    def selected_group_keys(self):"
if marker not in text:
    raise SystemExit("selected_group_keys() niet gevonden")

method = '''    def play_double_clicked(self, item):\n        data = item.data(Qt.ItemDataRole.UserRole)\n        if not isinstance(data, dict):\n            return\n        if data.get("kind") != "file":\n            return\n\n        path = str(data.get("path") or "").strip()\n        if not path:\n            return\n\n        file_path = Path(path)\n        if not file_path.is_file():\n            QMessageBox.warning(\n                self,\n                "MP3 ontbreekt",\n                f"Bestand bestaat niet meer:\\n\\n{path}",\n            )\n            return\n\n        # Open/play through the same Windows multimedia association used\n        # for MP3 files. This leaves multi-selection untouched.\n        QDesktopServices.openUrl(\n            QUrl.fromLocalFile(str(file_path))\n        )\n\n'''

if "def play_double_clicked" not in text:
    text = text.replace(marker, method + marker)

p.write_text(text, encoding="utf-8-sig")
print("OK: dubbelklik op een MP3-regel speelt de track af.")
