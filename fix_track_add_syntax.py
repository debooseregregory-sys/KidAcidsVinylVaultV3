from pathlib import Path

path = Path("gui/release_detail_page.py")

text = path.read_text(encoding="utf-8")

text = text.replace(
    '''                    "De nieuwe track kon niet worden "
                    "toegevoegd.

"
                    f"{exc}"
''',
    '''                    "De nieuwe track kon niet worden "
                    "toegevoegd.\\n\\n"
                    f"{exc}"
'''
)

text = text.replace(
    '''                "Track toegevoegd",
            (
                "De track is toegevoegd.

"
                f"{position} - {title}"
            )
''',
    '''                "Track toegevoegd",
            (
                "De track is toegevoegd.\\n\\n"
                f"{position} - {title}"
            )
'''
)

path.write_text(
    text,
    encoding="utf-8"
)

print()
print("=" * 60)
print("SYNTAX HERSTELD")
print("=" * 60)
print()
print("release_detail_page.py is aangepast.")
print()
print("Test nu:")
print("python .\\run_v3.py")
print("=" * 60)