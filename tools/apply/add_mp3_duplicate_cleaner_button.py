from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "gui" / "mp3_library_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

import_marker = "from database.database import get_connection\n"
import_line = "from gui.mp3_duplicate_cleaner import MP3DuplicateCleaner\n"
if import_line not in text:
    if import_marker not in text:
        raise RuntimeError("database import niet gevonden")
    text = text.replace(import_marker, import_marker + import_line, 1)

button_marker = '        self.meta_button = QPushButton("METADATA BEWERKEN")\n'
button_insert = button_marker + '''        self.duplicates_button = QPushButton("DUBBELE MP3'S")
        actions.addWidget(self.duplicates_button)
'''
if "self.duplicates_button = QPushButton" not in text:
    if button_marker not in text:
        raise RuntimeError("metadata button niet gevonden")
    text = text.replace(button_marker, button_insert, 1)

connect_marker = "        self.meta_button.clicked.connect(self.edit_selected_metadata)\n"
connect_insert = connect_marker + '''        self.duplicates_button.clicked.connect(self.open_duplicate_cleaner)
'''
if "self.duplicates_button.clicked.connect" not in text:
    if connect_marker not in text:
        raise RuntimeError("metadata button connect niet gevonden")
    text = text.replace(connect_marker, connect_insert, 1)

method_marker = "    def load_data(self):\n"
method = '''    def open_duplicate_cleaner(self):
        dialog = MP3DuplicateCleaner(self)
        dialog.exec()
        self.load_data()

'''
if "def open_duplicate_cleaner" not in text:
    if method_marker not in text:
        raise RuntimeError("load_data niet gevonden")
    text = text.replace(method_marker, method + method_marker, 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("DUBBELE MP3'S knop toegevoegd")
