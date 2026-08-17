from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_board_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

marker = '''    def schedule_search(self, _text=""):\n        self.search_timer.start()\n'''

if text.count(marker) != 1:
    raise RuntimeError(
        f"schedule_search marker verwacht 1 keer, gevonden {text.count(marker)}"
    )

insert = '''    def showEvent(self, event):\n        super().showEvent(event)\n\n        # Bij de eerste opening is de sidebar/layout soms nog niet volledig\n        # uitgewerkt. Qt berekent dan tijdelijk een te kleine viewport, waardoor\n        # de Board als een smal raster verschijnt. Na het tonen forceren we\n        # alleen een nieuwe kolomberekening en herschikken we de reeds geladen\n        # kaarten. Er worden geen nieuwe releases geladen.\n        QTimer.singleShot(0, self.refresh_initial_layout)\n        QTimer.singleShot(120, self.refresh_initial_layout)\n\n    def refresh_initial_layout(self):\n        if not hasattr(self, "scroll"):\n            return\n\n        columns = self.calculate_columns()\n        if columns == self._last_columns:\n            return\n\n        self._last_columns = 0\n\n        if hasattr(self, "_visible_rows"):\n            rows = list(self._visible_rows)\n        else:\n            rows = self.filtered_rows() if hasattr(self, "all_releases") else []\n\n        if rows:\n            self.populate(rows)\n        else:\n            self.grid.invalidate()\n            self.grid.activate()\n            self.container.adjustSize()\n            self.scroll.viewport().update()\n\n'''

text = text.replace(marker, insert + marker)
TARGET.write_text(text, encoding="utf-8")
print("RELEASE BOARD INITIELE LAYOUT REFRESH TOEGEVOEGD")
print("De Board berekent zijn kolommen opnieuw nadat het venster echt zichtbaar is.")
