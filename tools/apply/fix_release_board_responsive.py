from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PAGE = BASE / "gui" / "release_board_page.py"
TILE = BASE / "gui" / "release_board_tile.py"

page = PAGE.read_text(encoding="utf-8-sig")
tile = TILE.read_text(encoding="utf-8-sig")

old_tile_size = '''        self.setMinimumWidth(250)\n        self.setMaximumWidth(310)\n        self.setMinimumHeight(390)\n'''
new_tile_size = '''        self.setFixedWidth(250)\n        self.setFixedHeight(390)\n'''
if page.count(old_tile_size) != 0:
    raise RuntimeError("unexpected tile sizing found in page")
if tile.count(old_tile_size) != 1:
    raise RuntimeError(f"tile sizing block expected once, found {tile.count(old_tile_size)}")
tile = tile.replace(old_tile_size, new_tile_size)

old_resize = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n        columns = self.calculate_columns()\n        if columns != self._last_columns:\n            self._last_columns = columns\n            if hasattr(self, "_visible_rows") and self._visible_rows:\n                self.start_population(self._visible_rows)\n'''
new_resize = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n        QTimer.singleShot(0, self.reflow_loaded_tiles)\n\n    def reflow_loaded_tiles(self):\n        if not hasattr(self, "grid"):\n            return\n\n        widgets = []\n        while self.grid.count():\n            item = self.grid.takeAt(0)\n            widget = item.widget()\n            if widget is not None:\n                widgets.append(widget)\n\n        columns = max(1, self.calculate_columns())\n        self._last_columns = columns\n\n        for index, widget in enumerate(widgets):\n            self.grid.addWidget(widget, index // columns, index % columns)\n'''
if page.count(old_resize) != 1:
    raise RuntimeError(f"resize block expected once, found {page.count(old_resize)}")
page = page.replace(old_resize, new_resize)

old_calc = '''    def calculate_columns(self):\n        width = max(520, self.scroll.viewport().width() - 20)\n        return max(1, width // 270)\n'''
new_calc = '''    def calculate_columns(self):\n        available = max(250, self.scroll.viewport().width() - 28)\n        return max(1, available // 264)\n'''
if page.count(old_calc) != 1:
    raise RuntimeError(f"column block expected once, found {page.count(old_calc)}")
page = page.replace(old_calc, new_calc)

PAGE.write_text(page, encoding="utf-8")
TILE.write_text(tile, encoding="utf-8")

print("RELEASE BOARD IS NU RESPONSIEF")
print("Kaarten behouden dezelfde grootte; alleen het aantal kolommen verandert bij resize.")
