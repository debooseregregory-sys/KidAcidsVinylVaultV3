from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
s = p.read_text(encoding='utf-8-sig')

# Ensure mutagen duration fallback import.
if 'from mutagen.mp3 import MP3' not in s:
    s = s.replace('from database.database import get_connection\n', 'from database.database import get_connection\n\ntry:\n    from mutagen.mp3 import MP3\nexcept ImportError:\n    MP3 = None\n')

# Add duration to the worker SELECT if missing.
if 'm.duration' not in s[s.find('SELECT'):s.find('FROM mp3_files')]:
    s = s.replace('                        m.year,\n', '                        m.year,\n                        m.duration,\n')
    s = s.replace('                mp3_id, path, artist, title, album, year, checked, linked = row\n', '                mp3_id, path, artist, title, album, year, duration, checked, linked = row\n')
    s = s.replace('                            "year": year,\n', '                            "year": year,\n                            "duration": duration,\n')

# If duration key is absent in the member dictionaries, inject it after year.
if '"duration": duration' not in s:
    s = s.replace('                            "year": year,\n', '                            "year": year,\n                            "duration": duration,\n')

# Replace the visible row label construction with duration + full path.
old = '''                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name}"\n                )'''
new = '''                duration = member.get("duration")\n                try:\n                    total_seconds = int(round(float(duration)))\n                    duration_text = f"{total_seconds // 60}:{total_seconds % 60:02d}"\n                except Exception:\n                    duration_text = "--:--"\n\n                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name} | DUUR {duration_text} | "\n                    f"PAD: {member['path']}"\n                )'''
if old in s:
    s = s.replace(old, new)

# Fallback: if the simpler label variant is present, replace it too.
old2 = '                label = f"    {Path(member[\'path\']).name}"\n'
if old2 in s and 'DUUR {duration_text}' not in s:
    s = s.replace(old2, '                duration = member.get("duration")\n                try:\n                    total_seconds = int(round(float(duration)))\n                    duration_text = f"{total_seconds // 60}:{total_seconds % 60:02d}"\n                except Exception:\n                    duration_text = "--:--"\n                label = f"    {Path(member[\'path\']).name} | DUUR {duration_text} | PAD: {member[\'path\']}"\n')

# Add real playback on double-click using the local player signal if available.
if 'self.list.itemDoubleClicked.connect(self._play_double_clicked)' not in s:
    marker = '        self.list.itemSelectionChanged.connect(self.refresh_button_state)'
    if marker in s:
        s = s.replace(marker, marker + '\n        self.list.itemDoubleClicked.connect(self._play_double_clicked)')
    elif 'self.list.itemSelectionChanged.connect(self.on_selection_changed)' in s:
        s = s.replace('        self.list.itemSelectionChanged.connect(self.on_selection_changed)', '        self.list.itemSelectionChanged.connect(self.refresh_button_state)\n        self.list.itemDoubleClicked.connect(self._play_double_clicked)')

if 'def _play_double_clicked' not in s:
    insert_at = s.find('    def closeEvent(self, event):')
    method = '''    def _play_double_clicked(self, item):\n        data = item.data(Qt.ItemDataRole.UserRole)\n        if not isinstance(data, dict) or data.get("kind") != "file":\n            return\n        path = str(data.get("path") or "")\n        if not path or not Path(path).is_file():\n            return\n        parent = self.parent()\n        if parent is not None and hasattr(parent, "play_mp3"):\n            try:\n                parent.play_mp3(path)\n                return\n            except Exception:\n                pass\n        try:\n            import os\n            os.startfile(path)\n        except Exception as exc:\n            QMessageBox.warning(self, "Afspelen mislukt", str(exc))\n\n'''
    if insert_at >= 0:
        s = s[:insert_at] + method + s[insert_at:]

p.write_text(s, encoding='utf-8-sig')
print('OK: duur en volledig pad toegevoegd aan duplicate-cleaner.')
