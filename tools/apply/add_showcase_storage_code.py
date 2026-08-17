from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_showcase_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''        if release[6]: meta.append(str(release[6]))
        meta_label = QLabel(" • ".join(meta))
'''
new = '''        if release[6]: meta.append(str(release[6]))
        if release[11]:
            meta.append(f"KAST: {release[11]}")
        meta_label = QLabel(" • ".join(meta))
'''

if text.count(old) != 1:
    raise RuntimeError(f"Showcase meta-blok niet exact gevonden: {text.count(old)}")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")
print("SHOWCASE KASTCODE TOEGEVOEGD")
