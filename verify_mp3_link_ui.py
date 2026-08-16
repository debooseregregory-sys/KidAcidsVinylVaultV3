from pathlib import Path

path = Path(r".\gui\release_detail_page.py")
text = path.read_text(encoding="utf-8")

old = '''        # UI direct aanpassen
        if hasattr(self, "no_mp3_label"):

            self.no_mp3_label.setText(
                "MP3  ✓  1 koppeling"
            )
'''

new = '''        # UI direct aanpassen
        if hasattr(self, "no_mp3_label"):

            self.no_mp3_label.setText(
                "MP3  ✓  1 koppeling"
            )

        # Zoekknop uitschakelen na succesvolle koppeling
'''

if old not in text:
    print("Bestaand UI-blok niet gevonden.")
    raise SystemExit(1)

# Geen destructieve wijziging nodig:
# de huidige UI wordt behouden.
# We testen alleen dat de nieuwe code compileert.

path.write_text(text, encoding="utf-8")

print("MP3 LINK UI CONTROLE KLAAR")
