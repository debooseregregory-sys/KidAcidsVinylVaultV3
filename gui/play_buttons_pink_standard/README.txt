VinylVault — play-knoppen naar roze standaard
================================================

Vervang in gui/ deze bestanden (backups zitten in dezelfde zip):

  cd_showcase_page.py
  release_showcase_page.py
  liveset_detail_page.py
  livesets_showcase_page.py
  compact_track_card.py

Wat verandert:
  - Rood (#6b1717) → roze vinyl (#2a1524 / #ff4fa3)
  - Groen bij playing (#1f7a3d) → roze blijft roze (#3a1a30)
  - Geen andere logica gewijzigd

Terugzetten:
  kopieer *.BACKUP terug naar de originele bestandsnaam in gui/

Eerst lokaal backup (aanbevolen):
  copy gui\cd_showcase_page.py gui\cd_showcase_page.py.BACKUP_LOKAAL
  (herhaal voor de andere 4)
