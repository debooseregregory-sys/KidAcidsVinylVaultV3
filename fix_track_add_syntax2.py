from pathlib import Path

path = Path("gui/release_detail_page.py")

text = path.read_text(encoding="utf-8")

old = '''                "De track is toegevoegd.

"
                f"{position} - {title}"
'''

new = '''                "De track is toegevoegd.\\n\\n"
                f"{position} - {title}"
'''

if old not in text:
    raise SystemExit(
        "FOUT: foutieve tekst niet gevonden."
    )

text = text.replace(
    old,
    new,
    1
)

path.write_text(
    text,
    encoding="utf-8"
)

print("KLAAR - syntax hersteld.")
print()
print("Start VinylVault met:")
print("python .\\run_v3.py")