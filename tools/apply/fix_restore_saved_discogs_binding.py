from pathlib import Path
import re

p = Path("gui/mp3_library_page.py")
text = p.read_text(encoding="utf-8-sig")

# Remove any staticmethod/classmethod decorator immediately before restore_saved_discogs.
text = re.sub(
    r"(?m)^\s*@(?:staticmethod|classmethod)\s*\n(?=\s*def restore_saved_discogs\(self\):)",
    "",
    text,
)

# Remove the misplaced call from the middle of __init__.
text = text.replace(
    "        self.status = QLabel(f\"Bestand: {self.path}\")\n        self.restore_saved_discogs()\n",
    "        self.status = QLabel(f\"Bestand: {self.path}\")\n",
    1,
)

# Insert the call once, after the dialog UI is fully built and buttons are added.
marker = "        layout.addWidget(buttons)\n"
if "        self.restore_saved_discogs()\n" not in text:
    if marker not in text:
        raise SystemExit("Kon einde van MetadataDialog.__init__ niet vinden.")
    text = text.replace(
        marker,
        marker + "        self.restore_saved_discogs()\n",
        1,
    )

p.write_text(text, encoding="utf-8-sig")
print("OK: restore_saved_discogs is nu een normale instance-methode en wordt pas na de dialog-opbouw aangeroepen.")
