from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "gui" / "mp3_showcase_page.py"
text = FILE.read_text(encoding="utf-8-sig")
backup = FILE.with_name("mp3_showcase_page_BEFORE_FINAL_VISUAL_FIX.py")
if not backup.exists():
    backup.write_text(text, encoding="utf-8")

# Center the platter and leave equal visual room on both sides.
old = '''        r = max(145.0, min((w - 250.0) * 0.46, (h - 150.0) * 0.45))\n        cx = min(w * 0.46, w - r - 100)\n        cy = 300 + max(0.0, h - 610.0) * 0.12\n'''
new = '''        r = max(145.0, min((w - 300.0) * 0.46, (h - 170.0) * 0.45))\n        cx = w * 0.50\n        cy = min(h * 0.48, h - r - 115)\n'''
if old not in text:
    raise SystemExit("Vinyl layout block not found")
text = text.replace(old, new, 1)

# The tonearm remains on the right: this is the old pitch-fader side.
# Move the pitch fader to the opposite/left side.
text = text.replace("        pitch_x = w - 43\n", "        pitch_x = 43\n", 1)

# Add a visible physical tonearm cradle beside the platter.
needle = '''        stylus = QPointF(\n            rest_stylus.x() + (play_stylus.x() - rest_stylus.x()) * self.arm_progress,\n            rest_stylus.y() + (play_stylus.y() - rest_stylus.y()) * self.arm_progress,\n        )\n'''
insert = needle + '''\n        # Physical tonearm rest/cradle.  In READY state the headshell sits\n        # beside the platter, not over the record.\n        rest_x = w - 138\n        rest_y = 165\n        p.setPen(QPen(QColor("#050607"), 3))\n        p.setBrush(QBrush(QColor("#22242a")))\n        p.drawRoundedRect(QRectF(rest_x - 18, rest_y - 7, 36, 14), 5, 5)\n        p.setPen(QPen(QColor("#777a83"), 2))\n        p.drawLine(QPointF(rest_x - 10, rest_y - 5), QPointF(rest_x + 10, rest_y - 5))\n        p.drawLine(QPointF(rest_x - 10, rest_y + 5), QPointF(rest_x + 10, rest_y + 5))\n        self._text(p, QRectF(rest_x - 45, rest_y + 12, 90, 16), "ARM REST", 7, MUTED, QFont.Weight.Bold, Qt.AlignmentFlag.AlignCenter)\n'''
if needle not in text:
    raise SystemExit("Stylus block not found")
text = text.replace(needle, insert, 1)

# Remove Unicode display glyphs that can render as boxes/garbled characters.
for old, new in {
    "33⅓ RPM   •   DIRECT DRIVE   •   STABLE PLATTER": "33 1/3 RPM   -   DIRECT DRIVE   -   STABLE PLATTER",
    "●  PLAYING": "PLAYING",
    "■  READY": "READY",
    "▶ PLAY": "PLAY",
    "◀ VORIGE": "VORIGE",
    "❚❚": "PAUSE",
}.items():
    text = text.replace(old, new)

# Keep the showcase columns, table and list dark even under the application's global style.
text = text.replace('''        root = QVBoxLayout(self)\n''', '''        self.setObjectName("mp3ShowcasePage")\n        root = QVBoxLayout(self)\n''', 1)

old_css = '''            QTableWidget{background:#101015;color:#f2f2f5;border:1px solid #2b2932;border-radius:7px;gridline-color:#24242d;}\n            QTableWidget::item{background:#101015;color:#f2f2f5;padding:6px;border-bottom:1px solid #22222a;}\n'''
new_css = '''            QTableWidget{background:#101015;color:#f2f2f5;border:1px solid #2b2932;border-radius:7px;gridline-color:#24242d;alternate-background-color:#101015;}\n            QTableWidget::viewport{background:#101015;}\n            QTableWidget::item{background:#101015;color:#f2f2f5;padding:6px;border-bottom:1px solid #22222a;}\n'''
text = text.replace(old_css, new_css, 1)

old_css = '''            QListWidget{background:#101015;color:#f2f2f5;border:1px solid #2b2932;border-radius:7px;}\n'''
new_css = '''            QListWidget{background:#101015;color:#f2f2f5;border:1px solid #2b2932;border-radius:7px;alternate-background-color:#101015;}\n            QListWidget::viewport{background:#101015;}\n'''
text = text.replace(old_css, new_css, 1)

FILE.write_text(text, encoding="utf-8")
print("Patched:", FILE)
print("Backup:", backup)
