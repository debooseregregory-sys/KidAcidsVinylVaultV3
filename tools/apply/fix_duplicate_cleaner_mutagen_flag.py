from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
text = p.read_text(encoding='utf-8-sig')

text = text.replace(
    'if MUTAGEN_AVAILABLE and MP3 is not None and path:',
    'if MP3 is not None and path:',
)

text = text.replace(
    'if MUTAGEN_AVAILABLE and path:',
    'if MP3 is not None and path:',
)

p.write_text(text, encoding='utf-8-sig')
print('OK: MUTAGEN_AVAILABLE dependency removed from duplicate cleaner.')
