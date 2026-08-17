from pathlib import Path

path = Path("gui/release_detail_page.py")
s = path.read_text(encoding="utf-8-sig")

needle = '''        release = data["release"]\n\n'''
insert = '''        release = data["release"]\n\n        # Restore the saved KLAAR state whenever a release is opened.\n        self.update_checked_button(\n            int(release["checked"] or 0)\n        )\n\n'''

if s.count(needle) != 1:
    raise RuntimeError(
        f"{path}: expected 1 occurrence of load-release marker, found {s.count(needle)}"
    )

if 'self.update_checked_button(\n            int(release["checked"] or 0)\n        )' in s:
    print("KLAAR-status wordt al geladen bij openen.")
else:
    s = s.replace(needle, insert, 1)
    path.write_text(s, encoding="utf-8-sig")
    print("KLAAR-status wordt nu geladen bij openen en navigeren.")
