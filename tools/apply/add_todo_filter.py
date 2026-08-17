from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "gui" / "release_library_page.py"

s = path.read_text(encoding="utf-8-sig")

# Make the filter name explicit.
s = s.replace(
    'self.todo_button = QPushButton(\n            "[ NOG TE DOEN ]"\n        )',
    'self.todo_button = QPushButton(\n            "[ ALLEEN NIET KLAAR ]"\n        )',
    1,
)

# Keep the selected status filter after pressing VERNIEUW.
old = '''        self.all_releases = rows\n\n        self.display_releases(\n            rows\n        )'''
new = '''        self.all_releases = rows\n\n        self.filter_releases(\n            self.search_input.text()\n        )'''

if s.count(old) != 1:
    raise RuntimeError(
        f"{path}: expected 1 load/display block, found {s.count(old)}"
    )
s = s.replace(old, new, 1)

# Add a clear active-state visual for the three filters.
needle = '''        status_filter_layout.addStretch()\n\n        layout.addLayout(\n            status_filter_layout\n        )'''
insert = '''        status_filter_layout.addStretch()\n\n        self.update_status_filter_buttons()\n\n        layout.addLayout(\n            status_filter_layout\n        )'''

if s.count(needle) != 1:
    raise RuntimeError(
        f"{path}: expected status filter layout block, found {s.count(needle)}"
    )
s = s.replace(needle, insert, 1)

# Update the active button whenever the filter changes.
old = '''        self.status_filter = status\n\n        self.filter_releases(\n            self.search_input.text()\n        )'''
new = '''        self.status_filter = status\n\n        self.update_status_filter_buttons()\n\n        self.filter_releases(\n            self.search_input.text()\n        )'''
if s.count(old) != 1:
    raise RuntimeError(
        f"{path}: expected set_status_filter block, found {s.count(old)}"
    )
s = s.replace(old, new, 1)

# Insert the button-state helper before FILTER RELEASES.
marker = '''    # ========================================================\n    # FILTER RELEASES\n    # ========================================================\n'''
method = '''    # ========================================================\n    # STATUS FILTER BUTTONS\n    # ========================================================\n\n    def update_status_filter_buttons(self):\n\n        active_style = (\n            "QPushButton {"\n            " background-color: #d84b91;"\n            " color: #ffffff;"\n            " border: 1px solid #f05ca4;"\n            "}"\n        )\n\n        normal_style = (\n            "QPushButton {"\n            " background-color: #222222;"\n            " color: #ffffff;"\n            " border: 1px solid #3a3a3a;"\n            "}"\n        )\n\n        buttons = {\n            "all": self.all_button,\n            "todo": self.todo_button,\n            "checked": self.checked_button,\n        }\n\n        for name, button in buttons.items():\n            button.setStyleSheet(\n                active_style if self.status_filter == name else normal_style\n            )\n\n'''
if s.count(marker) != 1:
    raise RuntimeError(
        f"{path}: expected FILTER RELEASES marker, found {s.count(marker)}"
    )
s = s.replace(marker, method + marker, 1)

path.write_text(s, encoding="utf-8-sig")
print("ALLEEN NIET KLAAR-filter toegevoegd.")
print("De filter blijft actief na VERNIEUW en de actieve filter wordt zichtbaar gemarkeerd.")
