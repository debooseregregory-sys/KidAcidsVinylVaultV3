from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "gui" / "release_library_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

old = '''            # Achtergrond transparant maken zodat de
            # stylesheet het geel niet opnieuw overschrijft.
            opt.backgroundBrush = Qt.BrushStyle.NoBrush

            # Tekst tekenen
            style = opt.widget.style() if opt.widget else None
'''
new = '''            # Forceer de achtergrond ook in Qt's geselecteerde toestand.
            # Anders kan QTableWidget:selection-background-color het geel overschrijven.
            opt.palette.setColor(
                QPalette.ColorRole.Base,
                QColor(255, 235, 150)
            )
            opt.palette.setColor(
                QPalette.ColorRole.AlternateBase,
                QColor(255, 235, 150)
            )
            opt.palette.setColor(
                QPalette.ColorRole.Highlight,
                QColor(255, 235, 150)
            )
            opt.palette.setColor(
                QPalette.ColorRole.HighlightedText,
                QColor(20, 20, 20)
            )
            opt.backgroundBrush = QColor(255, 235, 150)

            # Tekst tekenen
            style = opt.widget.style() if opt.widget else None
'''
if old not in text:
    raise SystemExit("Delegate-placeholder niet gevonden; bestand niet gewijzigd.")
text = text.replace(old, new, 1)

old_css = '''                selection-background-color: #383838;
                selection-color: #ffffff;
'''
new_css = '''                selection-background-color: #ffeb96;
                selection-color: #141414;
'''
if old_css not in text:
    raise SystemExit("Selection stylesheet niet gevonden; bestand niet gewijzigd.")
text = text.replace(old_css, new_css, 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("VINYL LIBRARY yellow/selection fix applied")
