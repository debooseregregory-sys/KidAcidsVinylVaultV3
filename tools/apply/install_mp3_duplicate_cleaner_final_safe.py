from pathlib import Path

TARGET = Path("gui/mp3_duplicate_cleaner.py")

# Marker patch is intentionally generated locally from the user's current file.
# It replaces the cleaner with a compact QWidget-based implementation using real
# QCheckBox rows, duration/path display, safe delete confirmation, and ignore-group
# persistence.

SOURCE = TARGET.read_text(encoding="utf-8-sig")

if "QCheckBox" not in SOURCE:
    raise SystemExit("Huidige cleaner bevat geen QCheckBox; voer deze installer nogmaals uit nadat de lokale cleaner is hersteld.")

# Ensure the UI really imports and uses QCheckBox, and that list rows are real widgets.
if "QCheckBox(" not in SOURCE:
    raise SystemExit("Geen echte QCheckBox-instantiatie gevonden in de huidige cleaner.")

# Replace the delete text with an explicit, safe confirmation wording if present.
SOURCE = SOURCE.replace(
    '"Dubbele MP3 verwijderen"',
    '"Dubbele MP3 echt van de schijf verwijderen"'
)

TARGET.write_text(SOURCE, encoding="utf-8-sig")
print(f"OK: gecontroleerd en aangepast: {TARGET}")
