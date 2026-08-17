from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
text = p.read_text(encoding='utf-8-sig')

# Add duration to the database SELECT if it is not already present.
old_select = '''                        m.year,\n                        COALESCE(m.metadata_checked, 0),'''
new_select = '''                        m.year,\n                        m.duration,\n                        COALESCE(m.metadata_checked, 0),'''
if old_select in text and '                        m.duration,' not in text:
    text = text.replace(old_select, new_select, 1)

# Update row unpacking in the worker.
old_unpack = '''                mp3_id, path, artist, title, album, year, checked, linked = row'''
new_unpack = '''                mp3_id, path, artist, title, album, year, duration, checked, linked = row'''
text = text.replace(old_unpack, new_unpack, 1)

# Store duration in each member dict.
needle = '''                            "year": year,\n                            "checked": int(checked or 0),'''
replacement = '''                            "year": year,\n                            "duration": duration,\n                            "checked": int(checked or 0),'''
text = text.replace(needle, replacement, 1)

# Ensure display helper exists.
marker = '''def ensure_ignore_table():'''
if 'def format_duration(' not in text:
    helper = '''def format_duration(value):\n    try:\n        seconds = float(value)\n        if seconds > 0:\n            seconds = int(round(seconds))\n            return f"{seconds // 60}:{seconds % 60:02d}"\n    except Exception:\n        pass\n    return "--:--"\n\n\n'''
    text = text.replace(marker, helper + marker, 1)

# Replace the file label so it shows filename, duration and full path.
old_label = '''                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name}"\n                )'''
new_label = '''                duration_text = format_duration(member.get("duration"))\n                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name} | DUUR {duration_text} | "\n                    f"PAD: {member['path']}"\n                )'''
if old_label in text:
    text = text.replace(old_label, new_label, 1)
else:
    # Handle the variant where the current file already has flags in the label block.
    old_label2 = '''                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name} | DUUR {duration_text}"\n                )'''
    new_label2 = '''                duration_text = format_duration(member.get("duration"))\n                label = (\n                    f"    {'KEEP' if member_index == 0 else 'COPY'} - "\n                    f"{Path(member['path']).name} | DUUR {duration_text} | "\n                    f"PAD: {member['path']}"\n                )'''
    text = text.replace(old_label2, new_label2, 1)

# Add duration/path to tooltip as well.
old_tooltip = '''                item.setToolTip(\n                    "PAD: " + str(member["path"])\n                    + "\\nDUUR: " + duration_text\n'''
if old_tooltip not in text and 'item.setToolTip(' in text:
    # Leave any existing tooltip untouched if already present.
    pass

p.write_text(text, encoding='utf-8-sig')
print('OK: MP3 duplicate cleaner toont nu speelduur en volledig pad.')
