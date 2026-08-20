from pathlib import Path

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

# Multi-select in QListWidget: Ctrl-click / Shift-click.
text = text.replace(
    "self.list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)",
    "self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)"
)
text = text.replace(
    'self.delete_button = QPushButton("[ GESELECTEERD BESTAND VERWIJDEREN ]")',
    'self.delete_button = QPushButton("[ GESELECTEERDE BESTANDEN VERWIJDEREN ]")'
)
text = text.replace(
    'self.ignore_button = QPushButton("[ GESELECTEERDE AANVINKEN = NEGEREN ]")',
    'self.ignore_button = QPushButton("[ GESELECTEERDE GROEPEN NEGEREN ]")'
)
text = text.replace(
    'self.unignore_button = QPushButton("[ GESELECTEERDE NEGEREN OPHEFFEN ]")',
    'self.unignore_button = QPushButton("[ GESELECTEERDE GROEPEN TERUGZETTEN ]")'
)

# Connect actions to multi-select handlers when the old names are present.
text = text.replace(
    'self.ignore_button.clicked.connect(self.ignore_checked_groups)',
    'self.ignore_button.clicked.connect(self.ignore_selected_groups)'
)
text = text.replace(
    'self.unignore_button.clicked.connect(self.unignore_checked_groups)',
    'self.unignore_button.clicked.connect(self.unignore_selected_groups)'
)
text = text.replace(
    'self.delete_button.clicked.connect(self.delete_selected_file)',
    'self.delete_button.clicked.connect(self.delete_selected_files)'
)

# Replace selection handler if it exists.
start = text.find('    def on_selection_changed(self):')
if start >= 0:
    end = text.find('\n    def ', start + 5)
    if end < 0:
        end = len(text)
    replacement = '''    def on_selection_changed(self):
        selected = self.list.selectedItems()
        file_count = 0
        group_count = 0
        protected_count = 0

        for item in selected:
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            kind = data.get("kind")
            if kind == "file":
                if data.get("linked"):
                    protected_count += 1
                else:
                    file_count += 1
            elif kind == "group":
                group_count += 1

        self.delete_button.setEnabled(file_count > 0)
        self.ignore_button.setEnabled(group_count > 0)
        self.unignore_button.setEnabled(group_count > 0)

        self.delete_button.setText(
            f"[ GESELECTEERDE BESTANDEN VERWIJDEREN ({file_count}) ]"
        )
        self.ignore_button.setText(
            f"[ GESELECTEERDE GROEPEN NEGEREN ({group_count}) ]"
        )
        self.unignore_button.setText(
            f"[ GESELECTEERDE GROEPEN TERUGZETTEN ({group_count}) ]"
        )

'''
    text = text[:start] + replacement + text[end + 1:]
else:
    # Add handler just before closeEvent.
    marker = '    def closeEvent(self, event):'
    if marker not in text:
        raise SystemExit('closeEvent niet gevonden; bestand is onverwacht opgebouwd.')
    replacement = '''    def on_selection_changed(self):
        selected = self.list.selectedItems()
        file_count = 0
        group_count = 0
        protected_count = 0
        for item in selected:
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") == "file":
                if data.get("linked"):
                    protected_count += 1
                else:
                    file_count += 1
            elif data.get("kind") == "group":
                group_count += 1
        self.delete_button.setEnabled(file_count > 0)
        self.ignore_button.setEnabled(group_count > 0)
        self.unignore_button.setEnabled(group_count > 0)
        self.delete_button.setText(f"[ GESELECTEERDE BESTANDEN VERWIJDEREN ({file_count}) ]")
        self.ignore_button.setText(f"[ GESELECTEERDE GROEPEN NEGEREN ({group_count}) ]")
        self.unignore_button.setText(f"[ GESELECTEERDE GROEPEN TERUGZETTEN ({group_count}) ]")

'''
    text = text.replace(marker, replacement + marker, 1)

# Replace old delete method with multi-file delete.
start = text.find('    def delete_selected_file(self):')
if start >= 0:
    end = text.find('\n    def ', start + 5)
    if end < 0:
        end = len(text)
    replacement = '''    def delete_selected_files(self):
        selected = []
        protected = []

        for item in self.list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") != "file":
                continue
            if data.get("linked"):
                protected.append(data)
            else:
                selected.append(data)

        if not selected:
            QMessageBox.information(
                self,
                "Geen bestanden",
                "Selecteer een of meer MP3-bestanden. Gekoppelde VinylVault-bestanden blijven beschermd.",
            )
            return

        preview = "\\n".join(d.get("path", "") for d in selected[:10])
        if len(selected) > 10:
            preview += f"\\n... en nog {len(selected) - 10} bestand(en)"

        answer = QMessageBox.question(
            self,
            "Definitief verwijderen",
            f"Je staat op het punt {len(selected)} MP3-bestand(en) ECHT van de schijf te verwijderen.\\n\\n{preview}\\n\\nDoorgaan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        deleted = 0
        errors = []
        conn = get_connection()
        try:
            for data in selected:
                path = str(data.get("path") or "")
                try:
                    Path(path).unlink()
                    conn.execute("DELETE FROM mp3_files WHERE id=?", (data.get("id"),))
                    deleted += 1
                except Exception as exc:
                    errors.append(f"{path}\\n{exc}")
            conn.commit()
        finally:
            conn.close()

        msg = f"{deleted} MP3-bestand(en) definitief van de schijf verwijderd."
        if protected:
            msg += f"\\n\\n{len(protected)} gekoppeld bestand(en) werden beschermd en niet verwijderd."
        if errors:
            msg += "\\n\\nNiet verwijderd:\\n" + "\\n\\n".join(errors[:5])
        QMessageBox.information(self, "Resultaat", msg)
        self.scan()

'''
    text = text[:start] + replacement + text[end + 1:]
else:
    raise SystemExit('delete_selected_file niet gevonden; bestand is onverwacht opgebouwd.')

# Replace group handlers with handlers based on selected group rows.
for old_name, new_name, action in [
    ('ignore_checked_groups', 'ignore_selected_groups', 'add'),
    ('unignore_checked_groups', 'unignore_selected_groups', 'remove'),
]:
    start = text.find(f'    def {old_name}(self):')
    if start >= 0:
        end = text.find('\n    def ', start + 5)
        if end < 0:
            end = len(text)
        if action == 'add':
            replacement = '''    def ignore_selected_groups(self):
        keys = set()
        for item in self.list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") == "group" and data.get("group_key"):
                keys.add(str(data["group_key"]))
        if not keys:
            return
        self.ignored_keys.update(keys)
        save_ignored_keys(self.ignored_keys)
        self.scan()

'''
        else:
            replacement = '''    def unignore_selected_groups(self):
        keys = set()
        for item in self.list.selectedItems():
            data = item.data(Qt.ItemDataRole.UserRole) or {}
            if data.get("kind") == "group" and data.get("group_key"):
                keys.add(str(data["group_key"]))
        if not keys:
            return
        self.ignored_keys.difference_update(keys)
        save_ignored_keys(self.ignored_keys)
        self.show_ignored.setChecked(True)
        self.scan()

'''
        text = text[:start] + replacement + text[end + 1:]

# Ensure item data uses group_key consistently if current code uses track_key.
text = text.replace('"group_key": group["group_key"]', '"group_key": group.get("group_key") or group.get("track_key") or ""')

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 duplicate cleaner ondersteunt nu multi-select voor bestanden en groepen.")
