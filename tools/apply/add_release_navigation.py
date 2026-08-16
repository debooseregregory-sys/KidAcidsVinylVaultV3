from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 occurrence, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


# ============================================================
# RELEASE LIBRARY
# ============================================================

library = ROOT / "gui" / "release_library_page.py"

replace_once(
    library,
    "    release_selected = Signal(int)\n",
    "    release_selected = Signal(int, object)\n",
)

replace_once(
    library,
    """        self.release_selected.emit(\n            release_id\n        )\n\n    # ========================================================\n    # OPEN SELECTED\n""",
    """        self.release_selected.emit(\n            release_id,\n            self.visible_release_ids()\n        )\n\n    # ========================================================\n    # OPEN SELECTED\n""",
)

replace_once(
    library,
    """        self.release_selected.emit(\n            release_id\n        )\n\n    # ========================================================\n    # REFRESH\n""",
    """        self.release_selected.emit(\n            release_id,\n            self.visible_release_ids()\n        )\n\n    # ========================================================\n    # REFRESH\n""",
)

marker = """    # ========================================================\n    # REFRESH\n"""
insert = """    # ========================================================\n    # VISIBLE RELEASE IDS\n    # ========================================================\n\n    def visible_release_ids(self):\n\n        release_ids = []\n\n        for row in range(\n            self.table.rowCount()\n        ):\n\n            item = self.table.item(\n                row,\n                0\n            )\n\n            if item is None:\n\n                continue\n\n            try:\n\n                release_ids.append(\n                    int(item.text())\n                )\n\n            except Exception:\n\n                continue\n\n        return release_ids\n\n"""
replace_once(library, marker, insert + marker)


# ============================================================
# RELEASE DETAIL
# ============================================================

detail = ROOT / "gui" / "release_detail_page.py"

replace_once(
    detail,
    """    back_requested = Signal()\n\n    play_mp3 = Signal(str)\n""",
    """    back_requested = Signal()\n\n    play_mp3 = Signal(str)\n\n    previous_requested = Signal()\n\n    next_requested = Signal()\n""",
)

replace_once(
    detail,
    """        self.release_id = None\n\n        self.editing = False\n""",
    """        self.release_id = None\n\n        self.navigation_ids = []\n\n        self.editing = False\n""",
)

replace_once(
    detail,
    """        top.addWidget(\n            self.back_button\n        )\n\n        top.addStretch()\n\n        self.edit_button = QPushButton(\n""",
    """        top.addWidget(\n            self.back_button\n        )\n\n        self.previous_button = QPushButton(\n            "[ ← VORIGE ]"\n        )\n\n        self.previous_button.setMinimumHeight(\n            38\n        )\n\n        self.previous_button.clicked.connect(\n            self.previous_release\n        )\n\n        top.addWidget(\n            self.previous_button\n        )\n\n        self.next_button = QPushButton(\n            "[ VOLGENDE → ]"\n        )\n\n        self.next_button.setMinimumHeight(\n            38\n        )\n\n        self.next_button.clicked.connect(\n            self.next_release\n        )\n\n        top.addWidget(\n            self.next_button\n        )\n\n        top.addStretch()\n\n        self.edit_button = QPushButton(\n""",
)

replace_once(
    detail,
    """        self.edit_button.setText(\n            "[ BEWERKEN ]"\n        )\n\n        data = get_release_details(\n""",
    """        self.edit_button.setText(\n            "[ BEWERKEN ]"\n        )\n\n        self.update_navigation_buttons()\n\n        data = get_release_details(\n""",
)

marker = """    # ========================================================\n    # LOAD RELEASE\n"""
insert = """    # ========================================================\n    # RELEASE NAVIGATION\n    # ========================================================\n\n    def set_navigation_ids(\n        self,\n        release_ids\n    ):\n\n        self.navigation_ids = [\n            int(release_id)\n            for release_id in (release_ids or [])\n        ]\n\n        self.update_navigation_buttons()\n\n    def update_navigation_buttons(self):\n\n        if self.release_id is None:\n\n            self.previous_button.setEnabled(False)\n            self.next_button.setEnabled(False)\n            return\n\n        try:\n            index = self.navigation_ids.index(\n                int(self.release_id)\n            )\n        except ValueError:\n            self.previous_button.setEnabled(False)\n            self.next_button.setEnabled(False)\n            return\n\n        self.previous_button.setEnabled(\n            index > 0\n        )\n\n        self.next_button.setEnabled(\n            index < len(self.navigation_ids) - 1\n        )\n\n    def _navigate_to_index(\n        self,\n        index\n    ):\n\n        if self.editing:\n\n            answer = QMessageBox.question(\n                self,\n                "Niet opgeslagen",\n                "Er staan nog wijzigingen open. Eerst opslaan?",\n                QMessageBox.StandardButton.Yes\n                | QMessageBox.StandardButton.No\n                | QMessageBox.StandardButton.Cancel,\n                QMessageBox.StandardButton.Yes\n            )\n\n            if answer == QMessageBox.StandardButton.Cancel:\n                return\n\n            if answer == QMessageBox.StandardButton.Yes:\n                self.save_release()\n\n                if self.editing:\n                    return\n\n            else:\n                self.cancel_edit()\n\n        if index < 0 or index >= len(self.navigation_ids):\n            return\n\n        self.load_release(\n            self.navigation_ids[index]\n        )\n\n    def previous_release(self):\n\n        if self.release_id is None:\n            return\n\n        try:\n            index = self.navigation_ids.index(\n                int(self.release_id)\n            )\n        except ValueError:\n            return\n\n        self._navigate_to_index(\n            index - 1\n        )\n\n    def next_release(self):\n\n        if self.release_id is None:\n            return\n\n        try:\n            index = self.navigation_ids.index(\n                int(self.release_id)\n            )\n        except ValueError:\n            return\n\n        self._navigate_to_index(\n            index + 1\n        )\n\n"""
replace_once(detail, marker, insert + marker)


# ============================================================
# MAIN WINDOW
# ============================================================

main = ROOT / "gui" / "main_window.py"

replace_once(
    main,
    """    def open_release(\n        self,\n        release_id\n    ):\n\n        self.detail_page.load_release(\n            release_id\n        )\n""",
    """    def open_release(\n        self,\n        release_id,\n        release_ids=None\n    ):\n\n        if release_ids is None:\n\n            release_ids = self.library_page.visible_release_ids()\n\n        self.detail_page.set_navigation_ids(\n            release_ids\n        )\n\n        self.detail_page.load_release(\n            release_id\n        )\n""",
)

print("Release navigation toegevoegd.")
print("Herstart daarna VinylVault met: python run_v3.py")
