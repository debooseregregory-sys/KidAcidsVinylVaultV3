from pathlib import Path

p = Path("gui/mp3_library_page.py")
text = p.read_text(encoding="utf-8-sig")

needle = "    def _candidate_text(result):"

if needle not in text:
    raise SystemExit("_candidate_text() niet gevonden")

# Add @staticmethod immediately before the method when missing.
old = needle
new = "    @staticmethod\n" + needle

if "    @staticmethod\n    def _candidate_text(result):" not in text:
    text = text.replace(old, new, 1)

p.write_text(text, encoding="utf-8-sig")
print("OK: _candidate_text() is nu een staticmethod.")
