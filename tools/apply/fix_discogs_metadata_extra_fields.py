from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
PAGE = BASE / 'gui' / 'mp3_library_page.py'
LOOKUP = BASE / 'gui' / 'discogs_mp3_lookup.py'

# Extend Discogs helpers with composer extraction.
text = LOOKUP.read_text(encoding='utf-8-sig')
if 'def composer_text(' not in text:
    addition = '''\n\ndef composer_text(release: dict, track: dict | None = None) -> str:\n    names = []\n\n    def collect(items):\n        for item in items or []:\n            if not isinstance(item, dict):\n                continue\n            role = str(item.get("role") or "").strip().lower()\n            name = str(item.get("name") or "").strip()\n            if name and "composer" in role:\n                names.append(name)\n\n    collect((track or {}).get("extraartists") or [])\n    collect(release.get("extraartists") or [])\n    return ", ".join(dict.fromkeys(names))\n'''
    text += addition
    LOOKUP.write_text(text, encoding='utf-8')

# Add import.
text = PAGE.read_text(encoding='utf-8-sig')
if 'composer_text,' not in text:
    old = '    release_format,\n)'
    new = '    release_format,\n    composer_text,\n)'
    if old in text:
        text = text.replace(old, new, 1)

# Fill Album Artist when a release is selected.
old = '        self.artist.setText(artist_names(self.release))\n        self.album.setText(str(self.release.get("title") or "").strip())'
new = '        release_artist = artist_names(self.release)\n        self.artist.setText(release_artist)\n        self.album_artist.setText(release_artist)\n        self.album.setText(str(self.release.get("title") or "").strip())'
if old in text:
    text = text.replace(old, new, 1)

# Apply composer for selected track and keep existing BPM untouched.
old = '        self.title.setText(str(track.get("title") or "").strip())\n        self.track.setText(str(track.get("position") or "").strip())'
new = '        self.title.setText(str(track.get("title") or "").strip())\n        self.track.setText(str(track.get("position") or "").strip())\n\n        composer = composer_text(self.release, track)\n        if composer:\n            self.composer.setText(composer)'
if old in text:
    text = text.replace(old, new, 1)

PAGE.write_text(text, encoding='utf-8')
print('Discogs Metadata Builder uitgebreid: Album Artist + Composer.')
print('BPM blijft afkomstig van de bestaande MP3-tag en wordt nooit door Discogs verzonnen.')
