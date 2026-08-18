from pathlib import Path
import re

p = Path("gui/mp3_showcase_page.py")
backup = p.with_name("mp3_showcase_page.py.before_vinyl_deck_fix")
text = p.read_text(encoding="utf-8-sig")
backup.write_text(text, encoding="utf-8-sig")

# Make the vinyl panel genuinely large and visually prominent.
text = text.replace(
    'self.vinyl_player_panel.setMinimumWidth(260)',
    'self.vinyl_player_panel.setMinimumWidth(360)',
)
text = text.replace(
    'self.vinyl_player_panel.setMaximumWidth(320)',
    'self.vinyl_player_panel.setMaximumWidth(460)',
)
text = text.replace(
    'self.vinyl_disc.setMinimumSize(220,220)',
    'self.vinyl_disc.setMinimumSize(320,320)',
)

# Replace the small generic vinyl styling with a stronger deck appearance.
text = re.sub(
    r'self\.vinyl_player_panel\.setStyleSheet\(""".*?"""\)',
    '''self.vinyl_player_panel.setStyleSheet("""
            QFrame {
                background:#101016;
                border:2px solid #302735;
                border-radius:14px;
            }
            QLabel { color:#f2f2f5; }
            QPushButton {
                background:#1b1b24;
                color:#fff;
                border:1px solid #403747;
                border-radius:8px;
                padding:12px 18px;
                font-size:13px;
                font-weight:800;
            }
            QPushButton:hover {
                border-color:#d84b91;
                background:#28212b;
            }
        """)''',
    text,
    count=1,
    flags=re.S,
)

# Give the deck labels stronger hierarchy.
text = text.replace(
    '"color:#d84b91;font-size:18px;font-weight:900;"',
    '"color:#d84b91;font-size:22px;font-weight:900;letter-spacing:1px;"',
    1,
)
text = text.replace(
    '"color:#d84b91;font-size:16px;font-weight:bold;"',
    '"color:#d84b91;font-size:18px;font-weight:800;"',
    1,
)
text = text.replace(
    '"color:#fff;font-size:20px;font-weight:800;"',
    '"color:#fff;font-size:24px;font-weight:900;"',
    1,
)
text = text.replace(
    '"color:#9b9ba6;font-size:12px;font-weight:bold;"',
    '"color:#aaaab3;font-size:13px;font-weight:900;"',
    1,
)

# Make sure the normal MP3 PLAY button still uses the existing VinylVault player.
play_method = '''    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.play_mp3.emit(path)

'''

pattern = r'    def play_current\(self\):.*?(?=    def |\Z)'
if re.search(pattern, text, flags=re.S):
    text = re.sub(pattern, play_method, text, count=1, flags=re.S)

# Reconnect the decorative vinyl PLAY button to the same working method.
if 'self.vinyl_play_button' in text:
    marker = '        self.vinyl_play_button.clicked.connect(self.play_current)'
    if marker not in text:
        anchor = '        self.vinyl_play_button = QPushButton("[ PLAY ]")'
        text = text.replace(
            anchor,
            anchor + '\n        self.vinyl_play_button.clicked.connect(self.play_current)',
            1,
        )

p.write_text(text, encoding="utf-8-sig")
print(f"OK: grote Vinyl Player hersteld en MP3 PLAY teruggekoppeld. Backup: {backup}")
