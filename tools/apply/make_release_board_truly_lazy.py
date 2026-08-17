from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_board_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

# Replace the existing batch/render state with explicit pagination.
old_state = '''        self.all_releases = []
        self._last_columns = 0
        self._visible_rows = []
        self._render_index = 0
        self._render_batch_size = 36
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(False)
        self._render_timer.setInterval(0)
        self._render_timer.timeout.connect(self.render_batch)

        self.search_timer = QTimer(self)
'''

new_state = '''        self.all_releases = []
        self._last_columns = 0
        self._visible_rows = []
        self._render_index = 0
        self._page_size = 30

        self.search_timer = QTimer(self)
'''

if text.count(old_state) != 1:
    raise RuntimeError(f"render-state verwacht 1 keer, gevonden {text.count(old_state)}")
text = text.replace(old_state, new_state)

# Do not auto-load before the UI is visible; use a tiny delayed load only.
old_init_end = '''        self.build_ui()
        QTimer.singleShot(100, self.load_releases)
'''
new_init_end = '''        self.build_ui()
        QTimer.singleShot(120, self.load_releases)
'''
if text.count(old_init_end) != 1:
    raise RuntimeError(f"init-einde verwacht 1 keer, gevonden {text.count(old_init_end)}")
text = text.replace(old_init_end, new_init_end)

# Remove scroll-triggered auto loading and add a load-more control.
old_scroll = '''        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
'''
new_scroll = '''        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
'''
if text.count(old_scroll) != 1:
    raise RuntimeError(f"scroll-blok verwacht 1 keer, gevonden {text.count(old_scroll)}")
# identical replacement is intentional; retained for structural validation.

old_scroll_end = '''        self.scroll.setWidget(self.container)
        self.scroll.verticalScrollBar().valueChanged.connect(self.on_scroll)
        layout.addWidget(self.scroll, 1)

        self.setStyleSheet(
'''
new_scroll_end = '''        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self.load_more_button = QPushButton("MEER RELEASES LADEN")
        self.load_more_button.setMinimumHeight(42)
        self.load_more_button.clicked.connect(self.load_more)
        self.load_more_button.setVisible(False)
        layout.addWidget(self.load_more_button)

        self.setStyleSheet(
'''
if text.count(old_scroll_end) != 1:
    raise RuntimeError(f"scroll-einde verwacht 1 keer, gevonden {text.count(old_scroll_end)}")
text = text.replace(old_scroll_end, new_scroll_end)

# Replace the entire rendering section.
start = text.index('    def clear_tiles(self):')
end = text.index('    def calculate_columns(self):', start)

new_population = '''    def clear_tiles(self):
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
        self.load_more_button.setVisible(bool(self._visible_rows))
        self.load_more(initial=True)

    def load_more(self, initial=False):
        if not self._visible_rows:
            self.load_more_button.setVisible(False)
            return

        columns = max(1, self.calculate_columns())
        self._last_columns = columns

        end = min(
            self._render_index + self._page_size,
            len(self._visible_rows),
        )

        for index in range(self._render_index, end):
            row = self._visible_rows[index]
            tile = ReleaseBoardTile(row)
            tile.open_release.connect(self.open_release.emit)
            tile.play_mp3.connect(self.play_mp3.emit)
            self.grid.addWidget(tile, index // columns, index % columns)

        self._render_index = end
        self.load_more_button.setVisible(
            self._render_index < len(self._visible_rows)
        )

        if not initial and self._render_index >= len(self._visible_rows):
            self.load_more_button.setText("ALLES GELADEN")
        elif self._render_index < len(self._visible_rows):
            remaining = len(self._visible_rows) - self._render_index
            self.load_more_button.setText(
                f"MEER RELEASES LADEN  ({remaining} over)"
            )

    def populate(self, rows):
        self.start_population(rows)

'''
text = text[:start] + new_population + text[end:]

# Resize should rebuild only the currently visible page, never the whole collection.
old_resize = '''    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = self.calculate_columns()
        if columns != self._last_columns:
            self._last_columns = columns
            if hasattr(self, "_visible_rows") and self._visible_rows:
                self.start_population(self._visible_rows)
'''
new_resize = '''    def resizeEvent(self, event):
        super().resizeEvent(event)
        columns = self.calculate_columns()
        if columns != self._last_columns and hasattr(self, "_visible_rows"):
            rows_to_keep = self._visible_rows[:self._render_index]
            if rows_to_keep:
                self.start_population(self._visible_rows)
'''
if text.count(old_resize) != 1:
    raise RuntimeError(f"resize-blok verwacht 1 keer, gevonden {text.count(old_resize)}")
text = text.replace(old_resize, new_resize)

TARGET.write_text(text, encoding="utf-8")
print("RELEASE BOARD IS NU ECHT LAZY")
print("30 tegels per keer; geen automatische volledige opbouw meer.")
