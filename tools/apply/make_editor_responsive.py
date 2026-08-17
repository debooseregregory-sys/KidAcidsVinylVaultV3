from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "release_detail_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# TrackCard: keep action buttons from crushing the track title
# on smaller windows. The buttons move below the metadata row.
# ------------------------------------------------------------
old = '''        # ----------------------------------------------------
        # TRACK EDIT
        # ----------------------------------------------------

        edit_button = QPushButton(
            "[ TRACK BEWERKEN ]"
        )

        edit_button.setMinimumWidth(
            175
        )

        edit_button.clicked.connect(
            self.edit_track
        )

        header.addWidget(
            edit_button
        )

        # ----------------------------------------------------
        # TRACK DELETE
        # ----------------------------------------------------

        delete_button = QPushButton(
            "[ TRACK VERWIJDEREN ]"
        )

        delete_button.setMinimumWidth(
            190
        )

        delete_button.clicked.connect(
            self.delete_track
        )

        header.addWidget(
            delete_button
        )

        layout.addLayout(
            header
        )
'''

new = '''        # ----------------------------------------------------
        # TRACK ACTIONS
        # ----------------------------------------------------

        edit_button = QPushButton(
            "[ TRACK BEWERKEN ]"
        )

        edit_button.setMinimumWidth(
            150
        )

        edit_button.clicked.connect(
            self.edit_track
        )

        delete_button = QPushButton(
            "[ TRACK VERWIJDEREN ]"
        )

        delete_button.setMinimumWidth(
            160
        )

        delete_button.clicked.connect(
            self.delete_track
        )

        actions = QHBoxLayout()
        actions.setSpacing(7)
        actions.addStretch()
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)

        layout.addLayout(
            header
        )

        self._track_header = header
        self._track_actions = actions
        self._edit_button = edit_button
        self._delete_button = delete_button

        layout.addLayout(
            actions
        )

        self._responsive_small = False
'''

if text.count(old) != 1:
    raise RuntimeError(
        f"TrackCard action blok niet uniek gevonden: {text.count(old)}"
    )

text = text.replace(old, new)

# Add a resize handler to TrackCard before the next class/function section.
anchor = '''    def edit_track(self):
'''
if text.count(anchor) != 1:
    raise RuntimeError("TrackCard edit_track anchor niet gevonden")

resize_code = '''    def resizeEvent(self, event):

        super().resizeEvent(event)

        # The action row stays below the metadata row. This means
        # the track title keeps usable width at any window size.
        # Keep the actions right-aligned for a clean desktop layout.
        self._track_actions.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

    # --------------------------------------------------------
    # TRACK EDIT
    # --------------------------------------------------------

'''
text = text.replace(anchor, resize_code + '''    def edit_track(self):
''', 1)

# Relax a few fixed minimum button widths in the release editor.
replacements = {
    'self.cover_button.setMinimumWidth(\n            180\n        )': 'self.cover_button.setMinimumWidth(\n            140\n        )',
    'self.checked_button.setMinimumWidth(\n            140\n        )': 'self.checked_button.setMinimumWidth(\n            120\n        )',
    'self.add_track_button.setMinimumWidth(\n            190\n        )': 'self.add_track_button.setMinimumWidth(\n            160\n        )',
}
for old_piece, new_piece in replacements.items():
    if old_piece in text:
        text = text.replace(old_piece, new_piece, 1)

TARGET.write_text(text, encoding="utf-8")
print("EDITOR RESPONSIVE AANGEPAST")
print("Track-acties staan nu onder de trackinfo zodat titels niet meer worden samengedrukt.")
