from pathlib import Path
import re

p = Path('gui/main_window.py')
text = p.read_text(encoding='utf-8-sig')

# Start the main window maximized so MP3 Showcase is never initially laid out
# in the undersized/restored Windows geometry that causes the visual overlap.
if 'window.showMaximized()' not in text:
    pattern = r'(window\s*=\s*VinylVaultWindow\(\)\s*\n)'
    replacement = r'\1    window.showMaximized()\n'
    text, count = re.subn(pattern, replacement, text, count=1)
    if count == 0:
        raise SystemExit('VinylVaultWindow creation line not found in main_window.py')

p.write_text(text, encoding='utf-8-sig')
print('OK: VinylVault now starts maximized; MP3 Showcase avoids the initial small-window layout.')
