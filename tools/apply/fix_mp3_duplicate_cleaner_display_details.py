from pathlib import Path

path = Path('gui/mp3_duplicate_cleaner.py')
text = path.read_text(encoding='utf-8-sig')

# Add duration to the database query.
old = '''                        m.year,\n                        COALESCE(m.metadata_checked, 0),\n                        EXISTS(\n'''
new = '''                        m.year,\n                        m.duration,\n                        COALESCE(m.metadata_checked, 0),\n                        EXISTS(\n'''
if old in text and '                        m.duration,\n' not in text:
    text = text.replace(old, new, 1)

# Expand row unpacking in the worker.
text = text.replace(
    'mp3_id, path, artist, title, album, year, checked, linked = row',
    'mp3_id, path, artist, title, album, year, duration, checked, linked = row',
    1,
)

# Store duration in each member record.
old = '''                            "album": str(album or "").strip(),\n                            "year": year,\n                            "checked": int(checked or 0),\n'''
new = '''                            "album": str(album or "").strip(),\n                            "year": year,\n                            "duration": duration,\n                            "checked": int(checked or 0),\n'''
text = text.replace(old, new, 1)

# Replace Unicode-heavy display strings with ASCII-safe text and show full path + duration.
text = text.replace('DUBBEL GROEP {group_index}  •  ', 'DUBBEL GROEP {group_index} - ')
text = text.replace('  •  {artist} — {title}  •  {len(members)} BESTANDEN', ' - {artist} - {title} - {len(members)} BESTANDEN')
text = text.replace('f"    {\'★\' if member_index == 0 else \'•\'}  {Path(member[\'path\']).name}"', 'f"    {\'KEEP\' if member_index == 0 else \'COPY\'}  {Path(member[\'path\']).name}"')

# The current remote version uses a single line label block. Replace that block robustly.
old_block = '''                label = (\n                    f"    {'★' if member_index == 0 else '•'}  "\n                    f"{Path(member['path']).name}"\n                )\n\n                if member["album"]:\n                    label += f"  |  {member['album']}"\n                if member["year"]:\n                    label += f"  |  {member['year']}"\n                if flags:\n                    label += "  [" + " • ".join(flags) + "]"\n\n                item = QListWidgetItem(label)\n                item.setToolTip(member["path"])\n'''
new_block = '''                duration = member.get("duration")\n                try:\n                    duration_text = f"{float(duration):.0f} sec" if duration is not None else "duur onbekend"\n                except (TypeError, ValueError):\n                    duration_text = "duur onbekend"\n\n                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'}  "\n                    f"{Path(member['path']).name}  |  {duration_text}"\n                )\n\n                if flags:\n                    label += "  [" + " | ".join(flags) + "]"\n\n                item = QListWidgetItem(label)\n                item.setToolTip(\n                    f"Path: {member['path']}\\n"\n                    f"Artist: {member['artist']}\\n"\n                    f"Title: {member['title']}\\n"\n                    f"Album: {member['album']}\\n"\n                    f"Duration: {duration_text}"\n                )\n'''
if old_block in text:
    text = text.replace(old_block, new_block, 1)

# Make the dialog list show the full path as an additional second line.
needle = '                self.list.addItem(item)\n'
replacement = '''                item.setData(\n                    Qt.ItemDataRole.UserRole + 1,\n                    member["path"],\n                )\n                self.list.addItem(item)\n'''
text = text.replace(needle, replacement, 1)

path.write_text(text, encoding='utf-8-sig')
print('OK: duplicate cleaner toont nu duration en pad, met ASCII-veilige labels.')
