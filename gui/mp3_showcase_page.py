from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSizePolicy,
)

from database.database import get_connection

try:
    from mutagen.id3 import ID3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


def ensure_mp3_discogs_columns():
    conn = get_connection()
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        for name, kind in (("discogs_id", "TEXT"), ("discogs_link", "TEXT"), ("cover", "TEXT")):
            if name not in cols:
                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}")
        conn.commit()
    finally:
        conn.close()


class VinylDeckWidget(QWidget):
    """Visual turntable.  The arm is drawn as a real straight pivot arm."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_progress = 0.0
        self.pitch = 0.0
        self.setMinimumSize(620, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.setStyleSheet("background:#111117;border:1px solid #39313d;border-radius:18px;")

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
        self.arm_progress += (target - self.arm_progress) * 0.085
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
        p.drawText(QRectF(28, 24, 300, 26), Qt.AlignmentFlag.AlignLeft, "KID ACID'S VINYL VAULT")

        size = min(w * .68, h - 245)
        size = max(300.0, size)
        r = size / 2.0
        cx, cy = w * .42, 88 + r

        p.setPen(QPen(QColor("#55505a"), 2))
        p.setBrush(QBrush(QColor("#28262d")))
        p.drawEllipse(QPointF(cx, cy), r + 18, r + 18)
        p.setPen(QPen(QColor("#35323a"), 2))
        p.setBrush(QBrush(QColor("#0d0d11")))
        p.drawEllipse(QPointF(cx, cy), r + 7, r + 7)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setBrush(QBrush(QColor("#050508")))
        p.setPen(QPen(QColor("#26242b"), 1))
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
        p.setFont(QFont("Segoe UI", max(10, int(label_r/3.5)), QFont.Weight.Bold))
        p.drawText(QRectF(cx-label_r, cy-10, label_r*2, 20), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setPen(QPen(QColor("#c8c2ca"), 1))
        p.setBrush(QBrush(QColor("#d1cbd1")))
        p.drawEllipse(QPointF(cx, cy), 5, 5)

        # Tonearm: pivot -> straight arm -> headshell.  No artificial elbow bend.
        pivot = QPointF(w * .79, h * .235)
        rest_head = QPointF(w * .70, h * .36)
        groove_head = QPointF(cx + r * .76, cy - r * .10)
        hp = QPointF(
            rest_head.x() + (groove_head.x() - rest_head.x()) * self.arm_progress,
            rest_head.y() + (groove_head.y() - rest_head.y()) * self.arm_progress,
        )
        arm_vec = hp - pivot
        elbow = QPointF(pivot.x() + arm_vec.x() * .58, pivot.y() + arm_vec.y() * .58)

        p.setPen(QPen(QColor("#0a0a0c"), 8))
        p.drawLine(pivot, elbow)
        p.setPen(QPen(QColor("#bcb7bf"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, elbow)
        p.drawLine(elbow, hp)
        p.setPen(QPen(QColor("#6d6871"), 2))
        p.drawLine(pivot, elbow)

        p.setPen(QPen(QColor("#09090b"), 4))
        p.setBrush(QBrush(QColor("#3a3740")))
        p.drawEllipse(pivot, 23, 23)
        p.setPen(QPen(QColor("#bbb5bd"), 2))
        p.drawEllipse(pivot, 10, 10)

        # Headshell and stylus sit just above the outer groove, not on the label.
        p.setPen(QPen(QColor("#25232a"), 2))
        p.setBrush(QBrush(QColor("#d7d2d7")))
        p.drawRoundedRect(QRectF(hp.x()-28, hp.y()-9, 42, 18), 4, 4)
        p.setPen(QPen(QColor("#eeeeee"), 2))
        p.drawLine(QPointF(hp.x()-12, hp.y()+7), QPointF(hp.x()-16, hp.y()+24))
        p.setPen(QPen(QColor("#d84b91"), 2))
        p.drawPoint(QPointF(hp.x()-16, hp.y()+25))

        # Pitch slider is separate from the record and never overlaps the arm.
        px, py = w * .86, h * .58
        p.setPen(QPen(QColor("#57515b"), 2))
        p.setBrush(QBrush(QColor("#242229")))
        p.drawRoundedRect(QRectF(px-18, py-86, 36, 172), 9, 9)
        p.setPen(QColor("#aaa3ad"))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(px-45, py-116, 90, 20), Qt.AlignmentFlag.AlignCenter, "PITCH")
        knob_y = py - self.pitch * 2.0
        p.setBrush(QBrush(QColor("#d84b91")))
        p.setPen(QPen(QColor("#f0bfd5"), 1))
        p.drawRoundedRect(QRectF(px-12, knob_y-8, 24, 16), 4, 4)
        p.setPen(QColor("#77727c"))
        p.drawText(QRectF(px-45, py+96, 90, 20), Qt.AlignmentFlag.AlignCenter, f"{self.pitch:+.1f}%")

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


class MP3ShowcasePage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.visible_items = []
        self.current_index = -1
        self.build_ui()
        self.load_files()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        title = QLabel("MP3 SHOWCASE")
        title.setStyleSheet("font-size:25px;font-weight:900;color:#fff;")
        root.addWidget(title)

        search = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand...")
        search.addWidget(self.search)
        root.addLayout(search)

        self.status = QLabel("Laden...")
        self.status.setStyleSheet("color:#9b9ba6;")
        root.addWidget(self.status)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(14)

        self.list = QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["ARTIEST", "TRACK"])
        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list.setAlternatingRowColors(False)
        self.list.setMinimumWidth(520)
        self.list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        header = self.list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.list.verticalHeader().setDefaultSectionSize(32)
        self.list.itemSelectionChanged.connect(self._table_selection_changed)
        body.addWidget(self.list, 5)

        self.vinyl_deck = VinylDeckWidget(self)
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        body.addWidget(self.vinyl_deck, 6)

        right = QFrame()
        right.setMinimumWidth(300)
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cl = QVBoxLayout(right)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(8)

        self.cover = QLabel("GEEN COVER")
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setMinimumHeight(190)
        self.cover.setMaximumHeight(250)
        cl.addWidget(self.cover)

        self.info = QLabel("Geen track geselecteerd")
        self.info.setWordWrap(True)
        self.info.setTextFormat(Qt.TextFormat.RichText)
        cl.addWidget(self.info)

        tracks_title = QLabel("VINYLVAULT TRACKS")
        tracks_title.setStyleSheet("font-weight:900;color:#d84b91;")
        cl.addWidget(tracks_title)

        self.track_list = QListWidget()
        self.track_list.setMinimumHeight(140)
        self.track_list.itemDoubleClicked.connect(self.play_track_item)
        cl.addWidget(self.track_list, 1)

        controls = QHBoxLayout()
        self.previous = QPushButton("VORIGE")
        self.play = QPushButton("▶ PLAY")
        self.next = QPushButton("VOLGENDE")
        self.power = QPushButton("■ STOP")
        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        controls.addWidget(self.power)
        cl.addLayout(controls)
        body.addWidget(right, 3)
        root.addLayout(body, 1)

        self.search.textChanged.connect(self.populate_list)
        self.previous.clicked.connect(self.previous_track)
        self.play.clicked.connect(self.play_current)
        self.next.clicked.connect(self.next_track)
        self.power.clicked.connect(self.stop_current)

        self.setStyleSheet("""
        QWidget { background:#0b0b0f; color:#f2f2f5; }
        QLineEdit, QPushButton { background:#18181f; color:#fff; border:1px solid #30303a; border-radius:6px; padding:7px 10px; }
        QTableWidget { background:#101015; alternate-background-color:#101015; color:#f2f2f5; border:1px solid #2b2932; border-radius:7px; gridline-color:#24242d; }
        QTableWidget::item { background:#101015; color:#f2f2f5; padding:7px; border:0; border-bottom:1px solid #22222a; }
        QTableWidget::item:selected { background:#3a1d31; color:#fff; }
        QHeaderView::section { background:#18181f; color:#d84b91; border:0; border-bottom:1px solid #35303a; padding:8px; font-weight:800; }
        QTableCornerButton::section { background:#18181f; border:0; }
        QListWidget { background:#101015; color:#f2f2f5; border:1px solid #2b2932; border-radius:7px; }
        QListWidget::item { background:#101015; color:#f2f2f5; padding:7px; border-bottom:1px solid #22222a; }
        QListWidget::item:selected { background:#3a1d31; color:#fff; }
        QPushButton:hover { border-color:#d84b91; background:#24242c; }
        """)

    def load_files(self):
        conn = get_connection()
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
            fields = ["id", "path", "artist", "title", "album", "genre"]
            fields = [f for f in fields if f in cols]
            rows = conn.execute(f"SELECT {', '.join(fields)} FROM mp3_files ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE").fetchall()
            self.items = [dict(row) for row in rows]
        finally:
            conn.close()
        self.populate_list()

    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [
            row for row in self.items
            if not q or q in " ".join(str(v or "") for v in row.values()).casefold()
        ]
        self.list.blockSignals(True)
        self.list.setRowCount(0)
        for row in self.visible_items:
            r = self.list.rowCount()
            self.list.insertRow(r)
            artist = str(row.get("artist") or "Onbekende artiest")
            title = str(row.get("title") or Path(str(row.get("path") or "")).stem)
            self.list.setItem(r, 0, QTableWidgetItem(artist))
            self.list.setItem(r, 1, QTableWidgetItem(title))
        self.list.blockSignals(False)
        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items:
            self.list.selectRow(0)
        else:
            self.current_index = -1
            self.clear_showcase()

    def _table_selection_changed(self):
        self.select_index(self.list.currentRow())

    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            row = self.visible_items[index]
            artist = str(row.get("artist") or "Onbekende artiest")
            title = str(row.get("title") or Path(str(row.get("path") or "")).stem)
            self.vinyl_deck.set_track(artist, title)
            self.vinyl_deck.set_playing(False)
            self.show_item(row)

    def _release_context(self, mp3_id):
        if not mp3_id:
            return None, []
        conn = get_connection()
        try:
            tm_cols = {r[1] for r in conn.execute("PRAGMA table_info(track_mp3)").fetchall()}
            if "track_id" not in tm_cols:
                return None, []
            mp3_col = "mp3_id" if "mp3_id" in tm_cols else ("mp3_file_id" if "mp3_file_id" in tm_cols else None)
            if not mp3_col:
                return None, []
            release = conn.execute(f"""
                SELECT r.id, r.artist, r.title, r.label, r.catalog, r.year,
                       r.genre, r.discogs, r.discogs_link, r.cover
                FROM track_mp3 tm
                JOIN tracks t ON t.id = tm.track_id
                JOIN releases r ON r.id = t.release_id
                WHERE tm.{mp3_col} = ?
                ORDER BY t.id
                LIMIT 1
            """, (mp3_id,)).fetchone()
            if not release:
                return None, []
            tracks = conn.execute("""
                SELECT t.id, t.position, t.artist, t.title,
                       (SELECT mf.path
                        FROM track_mp3 tm2
                        JOIN mp3_files mf ON mf.id = tm2.mp3_id
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

    def show_item(self, row):
        artist = str(row.get("artist") or "Onbekende artiest")
        title = str(row.get("title") or Path(str(row.get("path") or "")).stem)
        release, tracks = self._release_context(row.get("id"))
        self.track_list.clear()

        if release:
            discogs = str(release["discogs"] or "")
            discogs_link = str(release["discogs_link"] or "")
            discogs_text = f"Discogs: {discogs}" if discogs else "Discogs: niet gekoppeld"
            if discogs_link:
                discogs_text += f"<br><a href='{discogs_link}'>Open Discogs</a>"
            info = (
                f"<b>{release['artist'] or artist}</b><br>{release['title'] or title}<br>"
                f"{release['label'] or ''} {release['catalog'] or ''}<br>"
                f"{release['year'] or ''}<br>{discogs_text}"
            )
            self.info.setText(info)
            self.info.setOpenExternalLinks(True)
            for track in tracks:
                pos = str(track["position"] or "")
                ta = str(track["artist"] or "")
                tt = str(track["title"] or "")
                text = "  ".join(x for x in (pos, ta, tt) if x)
                item = QListWidgetItem(text or "Onbekende track")
                if track["mp3_path"]:
                    item.setData(Qt.ItemDataRole.UserRole, str(track["mp3_path"]))
                self.track_list.addItem(item)
            self._show_cover(release["cover"], row.get("path"))
        else:
            self.info.setText(f"<b>{artist}</b><br>{title}<br><br>{Path(str(row.get('path') or '')).name}<br><br>Discogs: niet gekoppeld")
            self._show_cover("", row.get("path"))

        self.previous.setEnabled(self.current_index > 0)
        self.next.setEnabled(self.current_index + 1 < len(self.visible_items))
        self.play.setEnabled(True)

    def _show_cover(self, release_cover, mp3_path):
        pix = QPixmap()
        cover = str(release_cover or "").strip()
        if cover:
            cp = Path(cover)
            if not cp.is_absolute():
                cp = Path(__file__).resolve().parent.parent / cp
            if cp.exists():
                pix.load(str(cp))
        if pix.isNull() and MUTAGEN_AVAILABLE and mp3_path and Path(str(mp3_path)).exists():
            try:
                tags = ID3(str(mp3_path))
                for frame in tags.getall("APIC"):
                    pix.loadFromData(frame.data)
                    if not pix.isNull():
                        break
            except Exception:
                pass
        if pix.isNull():
            self.cover.setText("GEEN COVER")
            self.cover.setPixmap(QPixmap())
            return
        self.cover.setText("")
        self.cover.setPixmap(pix.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def clear_showcase(self):
        self.info.setText("Geen track geselecteerd")
        self.track_list.clear()
        self.cover.setPixmap(QPixmap())
        self.cover.setText("GEEN COVER")
        self.vinyl_deck.set_track("Onbekende artiest", "-")

    def _play_path(self, path):
        path = str(path or "")
        if not path or not Path(path).exists():
            self.status.setText("MP3-bestand niet gevonden")
            return False
        self.play_mp3.emit(path)
        window = self.window()
        if hasattr(window, "player_bar_play"):
            try:
                window.player_bar_play(path)
            except Exception:
                pass
        self.vinyl_deck.set_playing(True)
        return True

    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            self._play_path(self.visible_items[self.current_index].get("path"))

    def play_track_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._play_path(path)

    def stop_current(self):
        self.vinyl_deck.set_playing(False)
        window = self.window()
        if hasattr(window, "mp3_player"):
            try:
                window.mp3_player.stop()
            except Exception:
                pass

    def previous_track(self):
        if self.current_index > 0:
            self.list.selectRow(self.current_index - 1)
            self.play_current()

    def next_track(self):
        if self.current_index + 1 < len(self.visible_items):
            self.list.selectRow(self.current_index + 1)
            self.play_current()
