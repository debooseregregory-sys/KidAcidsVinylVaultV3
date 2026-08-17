from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
text = p.read_text(encoding='utf-8-sig')

# Add ignore/unignore buttons alongside the existing scan/delete buttons.
if 'self.ignore_button' not in text:
    text = text.replace(
        'self.delete_button = QPushButton("[ GESELECTEERDE BESTANDEN VERWIJDEREN ]")',
        'self.ignore_button = QPushButton("[ GESELECTEERDE GROEPEN NEGEREN ]")\n'
        '        self.unignore_button = QPushButton("[ GESELECTEERDE GROEPEN TERUGZETTEN ]")\n'
        '        self.delete_button = QPushButton("[ GESELECTEERDE BESTANDEN VERWIJDEREN ]")\n'
        '        self.ignore_button.setEnabled(False)\n'
        '        self.unignore_button.setEnabled(False)'
    )

if 'actions.addWidget(self.ignore_button)' not in text:
    text = text.replace(
        'actions.addWidget(self.delete_button)',
        'actions.addWidget(self.ignore_button)\n'
        '        actions.addWidget(self.unignore_button)\n'
        '        actions.addWidget(self.delete_button)'
    )

if 'self.ignore_button.clicked.connect' not in text:
    text = text.replace(
        'self.delete_button.clicked.connect(self.delete_files)',
        'self.ignore_button.clicked.connect(self.ignore_selected_groups)\n'
        '        self.unignore_button.clicked.connect(self.unignore_selected_groups)\n'
        '        self.delete_button.clicked.connect(self.delete_files)'
    )

# Insert helper methods before delete_files when possible.
if 'def ignore_selected_groups(self):' not in text:
    marker = '    def delete_files(self):\n'
    methods = '''    def _selected_groups(self):\n        groups = set()\n        for item in self.list.selectedItems():\n            data = item.data(Qt.ItemDataRole.UserRole) or {}\n            if data.get("kind") == "group":\n                groups.add(data.get("group_key") or data.get("track_key") or "")\n        return {g for g in groups if g}\n\n    def _refresh_button_state(self):\n        selected = self.list.selectedItems()\n        group_count = 0\n        file_count = 0\n        for item in selected:\n            data = item.data(Qt.ItemDataRole.UserRole) or {}\n            kind = data.get("kind")\n            if kind == "group":\n                group_count += 1\n            elif kind == "file" and not data.get("linked"):\n                file_count += 1\n\n        if hasattr(self, "ignore_button"):\n            self.ignore_button.setEnabled(group_count > 0)\n            self.unignore_button.setEnabled(group_count > 0)\n            self.ignore_button.setText(f"[ GESELECTEERDE GROEPEN NEGEREN ({group_count}) ]")\n            self.unignore_button.setText(f"[ NEGEREN OPHEFFEN ({group_count}) ]")\n        if hasattr(self, "delete_button"):\n            self.delete_button.setEnabled(file_count > 0)\n            self.delete_button.setText(f"[ GESELECTEERDE BESTANDEN VERWIJDEREN ({file_count}) ]")\n\n    def ignore_selected_groups(self):\n        keys = self._selected_groups()\n        if not keys:\n            QMessageBox.information(self, "Negeren", "Selecteer eerst een of meer GROEPEN.")\n            return\n        self.ignored_keys.update(keys)\n        save_ignored_keys(self.ignored_keys)\n        self.scan()\n\n    def unignore_selected_groups(self):\n        keys = self._selected_groups()\n        if not keys:\n            QMessageBox.information(self, "Negeren opheffen", "Selecteer eerst een of meer GROEPEN.")\n            return\n        self.ignored_keys.difference_update(keys)\n        save_ignored_keys(self.ignored_keys)\n        self.show_ignored.setChecked(True)\n        self.scan()\n\n'''
    if marker in text:
        text = text.replace(marker, methods + marker, 1)

# Ensure selection changes update buttons.
if 'self.list.itemSelectionChanged.connect' in text:
    import re
    text = re.sub(
        r'self\.list\.itemSelectionChanged\.connect\([^\n]+\)',
        'self.list.itemSelectionChanged.connect(self._refresh_button_state)',
        text,
        count=1,
    )
else:
    text = text.replace(
        'self.close_button.clicked.connect(self.close)',
        'self.list.itemSelectionChanged.connect(self._refresh_button_state)\n'
        '        self.close_button.clicked.connect(self.close)'
    )

# Multi-select is required.
text = text.replace(
    'QListWidget.SelectionMode.SingleSelection',
    'QListWidget.SelectionMode.ExtendedSelection'
)

p.write_text(text, encoding='utf-8-sig')
print('OK: multi-select + negeren/opheffen knoppen hersteld.')
