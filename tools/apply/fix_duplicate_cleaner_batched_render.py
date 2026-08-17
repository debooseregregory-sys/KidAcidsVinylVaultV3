from pathlib import Path

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

# QTimer is used to render the result list in small batches so the Qt GUI
# remains responsive even with thousands of duplicate rows.
if "QTimer" not in text:
    text = text.replace(
        "from PySide6.QtCore import Qt, QThread, Signal",
        "from PySide6.QtCore import Qt, QThread, Signal, QTimer",
        1,
    )

# Add render state after the existing closing flag.
needle = "        self._closing = False\n"
insert = (
    "        self._closing = False\n"
    "        self._render_queue = []\n"
    "        self._render_index = 0\n"
)
if "self._render_queue = []" not in text:
    if needle not in text:
        raise SystemExit("render state marker not found")
    text = text.replace(needle, insert, 1)

start = text.find("    def on_finished(self, groups):")
end = text.find("    def refresh_button_state(self):", start)
if start < 0 or end < 0:
    raise SystemExit("on_finished/refresh_button_state boundaries not found")

replacement = '''    def on_finished(self, groups):\n        if self._closing:\n            return\n\n        self.groups = groups or []\n        self.progress.setValue(100)\n        self.list.clear()\n        self.scan_button.setEnabled(True)\n        self.delete_button.setEnabled(False)\n        self.ignore_button.setEnabled(False)\n        self.unignore_button.setEnabled(False)\n\n        if not self.groups:\n            self.summary.setText(\n                f"Geen zichtbare dubbele groepen. {len(self.ignored_keys):,} groepen genegeerd."\n            )\n            return\n\n        duplicate_files = sum(\n            max(0, len(group["files"]) - 1)\n            for group in self.groups\n        )\n\n        # Build a lightweight render queue. The actual QListWidget rows are\n        # created in small chunks through QTimer so the GUI stays responsive.\n        self._render_queue = []\n        for group_index, group in enumerate(self.groups, 1):\n            self._render_queue.append(("group", group_index, group, None))\n            for member_index, member in enumerate(group["files"]):\n                self._render_queue.append((\"file\", group_index, group, member_index, member))\n\n        self._render_index = 0\n\n        self.summary.setText(\n            f"{len(self.groups):,} dubbele groepen | "\n            f"{duplicate_files:,} overtollige kopieen | "\n            f"{len(self.ignored_keys):,} genegeerd | resultaten worden geladen..."\n        )\n\n        QTimer.singleShot(0, self._render_next_batch)\n\n    def _render_next_batch(self):\n        if self._closing:\n            return\n\n        if not self._render_queue:\n            self.refresh_button_state()\n            return\n\n        batch_size = 40\n        end = min(\n            self._render_index + batch_size,\n            len(self._render_queue),\n        )\n\n        while self._render_index < end:\n            entry = self._render_queue[self._render_index]\n            kind = entry[0]\n            group_index = entry[1]\n            group = entry[2]\n\n            if kind == "group":\n                members = group["files"]\n                first = members[0]\n                artist = first["artist"] or "Onbekende artiest"\n                title = first["title"] or "Onbekende titel"\n                ignored = bool(group.get("ignored"))\n\n                header = QListWidgetItem(\n                    f"GROEP {group_index} - {artist} - {title} - {len(members)} BESTANDEN"\n                )\n                header.setData(\n                    Qt.ItemDataRole.UserRole,\n                    {\n                        "kind": "group",\n                        "group_key": group["key"],\n                        "ignored": ignored,\n                    },\n                )\n                self.list.addItem(header)\n\n            else:\n                member_index = entry[3]\n                member = entry[4]\n\n                duration_text = format_duration(member["duration"])\n                flags = []\n                if member["linked"]:\n                    flags.append("VINYL GEKOPPELD")\n                if member["checked"]:\n                    flags.append("METADATA KLAAR")\n                if member_index == 0:\n                    flags.append("EERSTE KOPIE")\n\n                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name} | DUUR {duration_text} | "\n                    f"PAD: {member['path']}"\n                )\n                if flags:\n                    label += " | " + " / ".join(flags)\n\n                item = QListWidgetItem(label)\n                item.setData(\n                    Qt.ItemDataRole.UserRole,\n                    {\n                        "kind": "file",\n                        "group_key": group["key"],\n                        "path": member["path"],\n                        "id": member["id"],\n                        "linked": bool(member["linked"]),\n                    },\n                )\n                item.setToolTip(\n                    "PAD: " + str(member["path"])\n                    + "\\nDUUR: " + duration_text\n                    + "\\nARTIST: " + str(member["artist"] or "")\n                    + "\\nTITEL: " + str(member["title"] or "")\n                )\n                self.list.addItem(item)\n\n            self._render_index += 1\n\n        if self._render_index < len(self._render_queue):\n            loaded = self._render_index\n            total = len(self._render_queue)\n            self.summary.setText(\n                f"Resultaten laden: {loaded:,} / {total:,} | "\n                f"{len(self.groups):,} dubbele groepen"\n            )\n            QTimer.singleShot(0, self._render_next_batch)\n        else:\n            duplicate_files = sum(\n                max(0, len(group["files"]) - 1)\n                for group in self.groups\n            )\n            self.summary.setText(\n                f"{len(self.groups):,} dubbele groepen gevonden | "\n                f"{duplicate_files:,} overtollige kopieen | "\n                f"{len(self.ignored_keys):,} genegeerd"\n            )\n            self.refresh_button_state()\n\n'''

text = text[:start] + replacement + text[end:]
p.write_text(text, encoding="utf-8-sig")
print("OK: duplicate cleaner now renders results in small GUI batches.")
