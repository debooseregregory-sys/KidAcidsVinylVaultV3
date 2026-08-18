from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"

text = TARGET.read_text(encoding="utf-8-sig")
old = '        p.drawText(QRectF(28,h-34,w-56,14),Qt.AlignmentFlag.AlignCenter,"KID ACID\'S VINYL VAULT")\n'
if old not in text:
    raise SystemExit("Onderste VinylVault-branding niet gevonden; bestand is NIET gewijzigd.")

text = text.replace(old, "", 1)
marker = '        p.drawRoundedRect(body, 18, 18)\n'
branding = '''\n        # Small permanent VinylVault branding in the upper-left corner.\n        p.setPen(QColor("#8d8790"))\n        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))\n        p.drawText(QRectF(34, 30, 230, 18), Qt.AlignmentFlag.AlignLeft, "KID ACID'S VINYL VAULT")\n'''
if marker not in text:
    raise SystemExit("Deck body marker niet gevonden; bestand is NIET gewijzigd.")
text = text.replace(marker, marker + branding, 1)
TARGET.write_text(text, encoding="utf-8-sig")
print("VinylVault-branding verplaatst naar linksboven.")
