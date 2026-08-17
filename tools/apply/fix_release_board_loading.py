from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_board_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old_init = '''        self.all_releases = []
        self._last_columns = 0

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.apply_search)

        self.build_ui()
        self.load_releases()
'''

new_init = '''        self.all_releases = []
        self._last_columns = 0
        self._visible_rows = []
        self._render_index = 0
        self._render_batch_size = 36
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(False)
        self._render_timer.setInterval(0)
        self._render_timer.timeout.connect(self.render_batch)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.apply_search)

        self.build_ui()
        QTimer.singleShot(100, self.load_releases)
'''

if text.count(old_init) != 1:
    raise RuntimeError(f"init-blok verwacht 1 keer, gevonden {text.count(old_init)}")
text = text.replace(old_init, new_init)

old_scroll = '''        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self.setStyleSheet(
'''

new_scroll = '''        self.scroll.setWidget(self.container)
        self.scroll.verticalScrollBar().valueChanged.connect(self.on_scroll)
        layout.addWidget(self.scroll, 1)

        self.setStyleSheet(
'''

if text.count(old_scroll) != 1:
    raise RuntimeError(f"scroll-blok verwacht 1 keer, gevonden {text.count(old_scroll)}")
text = text.replace(old_scroll, new_scroll)

old_load_end = '''        self.apply_search()

    def schedule_search(self, _text=""):
'''

new_load_end = '''        self.apply_search()

    def schedule_search(self, _text=""):
'''

if text.count(old_load_end) != 1:
    raise RuntimeError(f"load-end verwacht 1 keer, gevonden {text.count(old_load_end)}")

start = text.index('    def populate(self, rows):')
end = text.index('    def calculate_columns(self):', start)

new_population = '''    def clear_tiles(self):
        self._render_timer.stop()
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def start_population(self, rows):
        self.clear_tiles()
        self._visible_rows = list(rows)
        self._render_index = 0
        self.count_label.setText(f"{len(self._visible_rows)} releases")
        self._render_timer.start()

    def render_batch(self):
        if self._render_index >= len(self._visible_rows):
            self._render_timer.stop()
            return

        columns = max(1, self.calculate_columns())
        self._last_columns = columns

        end = min(
            self._render_index + self._render_batch_size,
            len(self._visible_rows),
        )

        for index in range(self._render_index, end):
            row = self._visible_rows[index]
            tile = ReleaseBoardTile(row)
            tile.open_release.connect(self.open_release.emit)
            tile.play_mp3.connect(self.play_mp3.emit)
            self.grid.addWidget(tile, index // columns, index % columns)

        self._render_index = end
        self.on_scroll(self.scroll.verticalScrollBar().value())

    def on_scroll(self, _value):
        bar = self.scroll.verticalScrollBar()
        remaining = bar.maximum() - bar.value()
        if remaining < max(900, self.scroll.viewport().height() * 2):
            if self._render_index < len(self._visible_rows):
                if not self._render_timer.isActive():
                    self._render_timer.start()

    def populate(self, rows):
        self.start_population(rows)

'''

text = text[:start] + new_population + text[end:]

old_resize = '''    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = self.calculate_columns()
        if columns != self._last_columns:
            self._last_columns = columns
            if hasattr(self, "all_releases"):
                self.populate(self.filtered_rows())
'''

new_resize = '''    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = self.calculate_columns()
        if columns != self._last_columns:
            self._last_columns = columns
            if hasattr(self, "_visible_rows") and self._visible_rows:
                self.start_population(self._visible_rows)
'''

if text.count(old_resize) != 1:
    raise RuntimeError(f"resize-blok verwacht 1 keer, gevonden {text.count(old_resize)}")
text = text.replace(old_resize, new_resize)

TARGET.write_text(text, encoding="utf-8")
print("RELEASE BOARD LAADT NU IN BATCHES")
print("De app opent eerst; covers/tegels worden daarna stapsgewijs opgebouwd.")
