from pathlib import Path

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

# Add checkbox behavior without changing the scan logic.
text = text.replace(
    'self.list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)',
    'self.list.setSelectionMode(QListWidget.SelectionMode.NoSelection)'
)

# Make file rows checkable when they are created.
needle = '''                item = QListWidgetItem(label)\n                item.setToolTip(member["path"])\n'''
repl = '''                item = QListWidgetItem(label)\n                item.setFlags(\n                    item.flags()\n                    | Qt.ItemFlag.ItemIsUserCheckable\n                    | Qt.ItemFlag.ItemIsSelectable\n                    | Qt.ItemFlag.ItemIsEnabled\n                )\n                item.setCheckState(Qt.CheckState.Unchecked)\n                item.setToolTip(member["path"])\n'''
if needle not in text:
    raise SystemExit("bestand-row niet gevonden")
text = text.replace(needle, repl, 1)

# Replace selection handler with checkbox-aware handler.
old = '''    def on_selection_changed(self):\n        selected = self.list.currentItem()\n        data = (\n            selected.data(Qt.ItemDataRole.UserRole)\n            if selected\n            else None\n        )\n        self.delete_button.setEnabled(\n            bool(\n                data\n                and data.get("kind") == "file"\n                and not data.get("linked")\n            )\n        )\n'''
new = '''    def on_selection_changed(self):\n        checked = 0\n        for row in range(self.list.count()):\n            item = self.list.item(row)\n            data = item.data(Qt.ItemDataRole.UserRole)\n            if data and data.get("kind") == "file" and item.checkState() == Qt.CheckState.Checked:\n                checked += 1\n        self.delete_button.setEnabled(checked > 0)\n'''
if old not in text:
    raise SystemExit("oude selectiehandler niet gevonden")
text = text.replace(old, new, 1)

# Replace delete_selected to delete ONLY checked files and explicitly warn that this is real disk deletion.
start = text.find('    def delete_selected(self):')
end = text.find('\n    def closeEvent(self, event):', start)
if start == -1 or end == -1:
    raise SystemExit("delete_selected blok niet gevonden")

new_delete = '''    def delete_selected(self):\n        checked = []\n        for row in range(self.list.count()):\n            item = self.list.item(row)\n            data = item.data(Qt.ItemDataRole.UserRole)\n            if not data or data.get("kind") != "file":\n                continue\n            if item.checkState() == Qt.CheckState.Checked:\n                checked.append((item, data))\n\n        if not checked:\n            return\n\n        protected = [data for item, data in checked if data.get("linked")]\n        deletable = [data for item, data in checked if not data.get("linked")]\n\n        if not deletable:\n            QMessageBox.warning(\n                self,\n                "Geen verwijderbare bestanden",\n                "Alle aangevinkte bestanden zijn aan VinylVault gekoppeld en worden beschermd."\n            )\n            return\n\n        paths = [str(data.get("path") or "") for data in deletable]\n        preview = "\\n\\n".join(paths[:10])\n        if len(paths) > 10:\n            preview += f"\\n\\n... en nog {len(paths) - 10} bestanden."\n\n        answer = QMessageBox.warning(\n            self,\n            "ECHT VAN DE SCHIJF VERWIJDEREN",\n            "De aangevinkte MP3-bestanden worden ECHT van je harde schijf verwijderd.\\n\\n"\n            + preview\n            + "\\n\\nWil je doorgaan?",\n            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,\n            QMessageBox.StandardButton.No,\n        )\n        if answer != QMessageBox.StandardButton.Yes:\n            return\n\n        failed = []\n        deleted_ids = []\n        try:\n            for data in deletable:\n                path = Path(str(data.get("path") or ""))\n                mp3_id = int(data.get("id"))\n                try:\n                    if path.exists():\n                        path.unlink()\n                    deleted_ids.append(mp3_id)\n                except Exception as exc:\n                    failed.append(f"{path} -> {exc}")\n\n            if deleted_ids:\n                conn = get_connection()\n                try:\n                    conn.executemany(\n                        "DELETE FROM mp3_files WHERE id=?",\n                        [(mp3_id,) for mp3_id in deleted_ids],\n                    )\n                    conn.commit()\n                finally:\n                    conn.close()\n\n        except Exception as exc:\n            QMessageBox.critical(self, "Verwijderen mislukt", str(exc))\n            return\n\n        if failed:\n            QMessageBox.warning(\n                self,\n                "Niet alles verwijderd",\n                "Sommige bestanden konden niet worden verwijderd:\\n\\n" + "\\n".join(failed[:10]),\n            )\n        else:\n            QMessageBox.information(\n                self,\n                "Verwijderd",\n                f"{len(deleted_ids)} MP3-bestand(en) zijn van de schijf verwijderd en uit de database gehaald."\n            )\n\n        self.scan()\n'''
text = text[:start] + new_delete + text[end:]

# Ensure checkbox state changes update the delete button.
if 'self.list.itemChanged.connect(self.on_selection_changed)' not in text:
    text = text.replace(
        'self.list.itemSelectionChanged.connect(self.on_selection_changed)',
        'self.list.itemChanged.connect(self.on_selection_changed)\n        self.list.itemSelectionChanged.connect(self.on_selection_changed)',
        1,
    )

p.write_text(text, encoding="utf-8-sig")
print("OK: checkbox-selectie en veilige echte verwijdering toegevoegd.")
