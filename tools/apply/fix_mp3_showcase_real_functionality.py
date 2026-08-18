from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# 1. Replace the deck with a mechanically simple, straight tonearm.
# ------------------------------------------------------------
start = text.index("class VinylDeckWidget(QWidget):")
end = text.index("\n\nclass MP3ShowcasePage(QWidget):", start)

deck = r'''class VinylDeckWidget(QWidget):
    """Clean visual turntable used by MP3 Showcase."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_progress = 0.0
        self.pitch = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.setMinimumSize(620, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_track(self, artist="", title=""):
        self.artist = str(artist or "Onbekende artiest")
        self.title = str(title or "Onbekende titel")
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing)
        if self.playing:
            self.timer.start()
        else:
            self.timer.start()
        self.update()

    def _tick(self):
        if self.playing:
            self.angle = (self.angle + 2.5) % 360.0
        target = 1.0 if self.playing else 0.0
        self.arm_progress += (target - self.arm_progress) * 0.12
        if not self.playing and self.arm_progress < 0.002:
            self.arm_progress = 0.0
            self.timer.stop()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        p.fillRect(self.rect(), QColor("#111117"))
        p.setPen(QPen(QColor("#4a414d"), 1))
        p.setBrush(QBrush(QColor("#191920")))
        p.drawRoundedRect(QRectF(10, 10, w - 20, h - 20), 18, 18)

        p.setPen(QColor("#d84b91"))
        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p.drawText(QRectF(28, 24, 360, 26), Qt.AlignmentFlag.AlignLeft, "KID ACID'S VINYL VAULT")

        size = min(w * .66, h - 250)
        r = max(270.0, size / 2.0)
        cx, cy = w * .42, 92 + r

        p.setPen(QPen(QColor("#55505a"), 2))
        p.setBrush(QBrush(QColor("#28262d")))
        p.drawEllipse(QPointF(cx, cy), r + 18, r + 18)
        p.setPen(QPen(QColor("#35323a"), 2))
        p.setBrush(QBrush(QColor("#0d0d11")))
        p.drawEllipse(QPointF(cx, cy), r + 7, r + 7)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor("#26242b"), 1))
        p.setBrush(QBrush(QColor("#050508")))
        p.drawEllipse(QPointF(0, 0), r, r)
        for f in (.94, .89, .84, .79, .74, .69, .64, .59, .54):
            rr = r * f
            p.setPen(QPen(QColor("#17171d"), 1))
            p.drawEllipse(QPointF(0, 0), rr, rr)
        p.setPen(QPen(QColor(216, 75, 145, 125), 3))
        p.drawArc(QRectF(-r*.83, -r*.83, r*1.66, r*1.66), 18*16, 78*16)
        p.restore()

        label_r = min(68.0, r * .24)
        p.setPen(QPen(QColor("#ee9fc2"), 2))
        p.setBrush(QBrush(QColor("#68183f")))
        p.drawEllipse(QPointF(cx, cy), label_r, label_r)
        p.setPen(QColor("#f7e6ee"))
        p.setFont(QFont("Segoe UI", max(10, int(label_r / 3.5)), QFont.Weight.Bold))
        p.drawText(QRectF(cx-label_r, cy-10, label_r*2, 20), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setPen(QPen(QColor("#c8c2ca"), 1))
        p.setBrush(QBrush(QColor("#d1cbd1")))
        p.drawEllipse(QPointF(cx, cy), 5, 5)

        # REALISTIC STRAIGHT TONEARM: one continuous shaft from pivot to headshell.
        pivot = QPointF(w * .79, h * .235)
        rest_head = QPointF(w * .68, h * .39)
        outer_groove = QPointF(cx + r * .79, cy - r * .05)
        hp = QPointF(
            rest_head.x() + (outer_groove.x() - rest_head.x()) * self.arm_progress,
            rest_head.y() + (outer_groove.y() - rest_head.y()) * self.arm_progress,
        )

        # Keep the arm straight.  The headshell is attached directly to the arm end.
        p.setPen(QPen(QColor("#08080a"), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, hp)
        p.setPen(QPen(QColor("#bdb8c0"), 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, hp)
        p.setPen(QPen(QColor("#69646d"), 2))
        p.drawLine(pivot, hp)

        p.setPen(QPen(QColor("#09090b"), 4))
        p.setBrush(QBrush(QColor("#3a3740")))
        p.drawEllipse(pivot, 23, 23)
        p.setPen(QPen(QColor("#c8c2ca"), 2))
        p.drawEllipse(pivot, 9, 9)

        # Headshell follows the arm direction and ends just inside the outer groove.
        vx, vy = hp.x() - pivot.x(), hp.y() - pivot.y()
        length = max(1.0, (vx * vx + vy * vy) ** 0.5)
        nx, ny = -vy / length, vx / length
        hx, hy = hp.x() + nx * 2, hp.y() + ny * 2
        p.save()
        p.translate(hx, hy)
        p.rotate(__import__("math").degrees(__import__("math").atan2(vy, vx)))
        p.setPen(QPen(QColor("#25232a"), 2))
        p.setBrush(QBrush(QColor("#d7d2d7")))
        p.drawRoundedRect(QRectF(-30, -8, 34, 16), 3, 3)
        p.setPen(QPen(QColor("#eeeeee"), 2))
        p.drawLine(QPointF(-4, 7), QPointF(-7, 20))
        p.setPen(QPen(QColor("#d84b91"), 2))
        p.drawPoint(QPointF(-7, 21))
        p.restore()

        # Pitch is deliberately isolated on the right side.
        px, py = w * .89, h * .55
        p.setPen(QPen(QColor("#57515b"), 2))
        p.setBrush(QBrush(QColor("#242229")))
        p.drawRoundedRect(QRectF(px-17, py-82, 34, 164), 8, 8)
        p.setPen(QColor("#aaa3ad"))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(px-45, py-110, 90, 20), Qt.AlignmentFlag.AlignCenter, "PITCH")
        knob_y = py - self.pitch * 2.0
        p.setBrush(QBrush(QColor("#d84b91")))
        p.setPen(QPen(QColor("#f0bfd5"), 1))
        p.drawRoundedRect(QRectF(px-11, knob_y-8, 22, 16), 4, 4)
        p.setPen(QColor("#77727c"))
        p.drawText(QRectF(px-45, py+91, 90, 20), Qt.AlignmentFlag.AlignCenter, f"{self.pitch:+.1f}%")

        p.setPen(QColor("#d84b91"))
        p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        p.drawText(QRectF(24, h-104, w-48, 22), Qt.AlignmentFlag.AlignCenter, self.artist)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        p.drawText(QRectF(24, h-78, w-48, 26), Qt.AlignmentFlag.AlignCenter, self.title)
        p.setPen(QColor("#78727c"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(24, h-48, w-48, 18), Qt.AlignmentFlag.AlignCenter, "KID ACID'S VINYL VAULT")
        p.end()
'''
text = text[:start] + deck + text[end:]

# ------------------------------------------------------------
# 2. Make release lookup tolerant of both historical track_mp3 schemas.
# ------------------------------------------------------------
old = re.search(r"    def _release_context\(self, mp3_id\):.*?\n    def show_item\(self, row\):", text, re.S)
if not old:
    raise SystemExit("release context block not found")

new = r'''    def _release_context(self, mp3_id):
        if not mp3_id:
            return None, []
        conn = get_connection()
        try:
            tm_cols = {r[1] for r in conn.execute("PRAGMA table_info(track_mp3)").fetchall()}
            mp3_col = "mp3_id" if "mp3_id" in tm_cols else ("mp3_file_id" if "mp3_file_id" in tm_cols else None)
            if "track_id" not in tm_cols or not mp3_col:
                return None, []

            release = conn.execute(f"""
                SELECT r.id, r.artist, r.title, r.label, r.catalog, r.year,
                       r.genre, r.discogs, r.discogs_link, r.cover
                FROM track_mp3 tm
                JOIN tracks t ON t.id = tm.track_id
                JOIN releases r ON r.id = t.release_id
                WHERE tm.{mp3_col} = ?
                LIMIT 1
            """, (mp3_id,)).fetchone()
            if not release:
                return None, []

            tracks = conn.execute(f"""
                SELECT t.id, t.position, t.artist, t.title,
                       (SELECT mf.path
                        FROM track_mp3 tm2
                        JOIN mp3_files mf ON mf.id = tm2.{mp3_col}
                        WHERE tm2.track_id = t.id
                        LIMIT 1) AS mp3_path
                FROM tracks t
                WHERE t.release_id = ?
                ORDER BY t.id
            """, (release["id"],)).fetchall()
            return release, tracks
        except Exception:
            return None, []
        finally:
            conn.close()

    def show_item(self, row):'''
text = text[:old.start()] + new + text[old.end():]

# ------------------------------------------------------------
# 3. Use the real MP3Player API.  The old code called methods that do not exist.
# ------------------------------------------------------------
old = re.search(r"    def _play_path\(self, path\):.*?\n    def play_current\(self\):", text, re.S)
if not old:
    raise SystemExit("play block not found")

new = r'''    def _play_path(self, path):
        path = str(path or "")
        if not path or not Path(path).exists():
            self.status.setText("MP3-bestand niet gevonden")
            return False
        window = self.window()
        player = getattr(window, "mp3_player", None)
        if player is None or not hasattr(player, "play_file"):
            self.status.setText("MP3-player niet beschikbaar")
            return False
        try:
            player.play_file(path)
        except Exception as exc:
            self.status.setText(f"Afspelen mislukt: {exc}")
            return False
        self.vinyl_deck.set_playing(True)
        self.status.setText("▶ Speelt af")
        return True

    def play_current(self):'''
text = text[:old.start()] + new + text[old.end():]

# Stop through the real player object too.
text = text.replace('''        if hasattr(window, "mp3_player"):
            try:
                window.mp3_player.stop()
            except Exception:
                pass''', '''        player = getattr(window, "mp3_player", None)
        if player is not None and hasattr(player, "stop"):
            try:
                player.stop()
            except Exception:
                pass
        self.status.setText("■ Gestopt")''')

# ------------------------------------------------------------
# 4. Make both track tables consistently dark.
# ------------------------------------------------------------
text = text.replace('''        QListWidget { background:#101015; color:#f2f2f5; border:1px solid #2b2932; border-radius:7px; }
        QListWidget::item { background:#101015; color:#f2f2f5; padding:7px; border-bottom:1px solid #22222a; }
        QListWidget::item:selected { background:#3a1d31; color:#fff; }''', '''        QFrame { background:#101015; color:#f2f2f5; }
        QListWidget { background:#101015; color:#f2f2f5; border:1px solid #2b2932; border-radius:7px; }
        QListWidget::item { background:#101015; color:#f2f2f5; padding:7px; border-bottom:1px solid #22222a; }
        QListWidget::item:selected { background:#3a1d31; color:#fff; }''')

TARGET.write_text(text, encoding="utf-8")
print("MP3 Showcase repaired:", TARGET)
