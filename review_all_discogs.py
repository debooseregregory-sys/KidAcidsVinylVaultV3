# ============================================================
# KID ACID'S VINYLVAULT V3
# FULL COLLECTION DISCOGS REVIEWER
# ============================================================
#
# - Alle releases worden gecontroleerd, ook bestaande Discogs-ID's.
# - Eerst lokale discogs_vinyl data.
# - Daarna live Discogs API als token beschikbaar is.
# - Label is een scorefactor, GEEN harde blokkade.
# - Bestaande koppeling wordt nooit automatisch gewijzigd.
# - Alleen een expliciete keuze van de gebruiker schrijft naar DB.
# - Voor de eerste wijziging wordt automatisch een backup gemaakt.
#
# ============================================================

import os
import re
import sys
import shutil
import sqlite3
import time
from datetime import datetime
from difflib import SequenceMatcher

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)


# ============================================================
# CONFIG
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DISCOGS_API = "https://api.discogs.com"
USER_AGENT = "KidAcidVinylVaultV3/1.0 (Full Collection Review)"
REQUEST_DELAY = 1.1
LIVE_RESULTS = 25
LOCAL_RESULTS = 25
MAX_CANDIDATES = 12


# ============================================================
# DATABASE PATH
# ============================================================

def find_database():
    candidates = [
        os.path.join(SCRIPT_DIR, "data", "vinylvault.db"),
        os.path.join(os.path.dirname(SCRIPT_DIR), "data", "vinylvault.db"),
        os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "data", "vinylvault.db"),
    ]
    for path in candidates:
        path = os.path.abspath(path)
        if os.path.exists(path):
            return path
    raise FileNotFoundError("vinylvault.db niet gevonden.\n\n" + "\n".join(candidates))


DB = find_database()


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize(value):
    if value is None:
        return ""
    text = str(value).lower().strip()
    text = text.replace("&", " and ")
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"[^a-z0-9à-ÿ]+", " ", text)
    return " ".join(text.split())


def normalize_artist(value):
    if value is None:
        return ""
    text = str(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"\bfeaturing\b", " feat ", text)
    text = re.sub(r"\bfeat\.?\b", " feat ", text)
    text = re.sub(r"[^a-z0-9à-ÿ]+", " ", text)
    return " ".join(text.split())


def normalize_label(value):
    if value is None:
        return ""
    text = str(value).lower().strip()
    text = text.replace("&", " and ")
    for suffix in (
        " records", " record", " recordings", " recording",
        " music", " label", " ltd", " limited", " inc", " bv", " b.v."
    ):
        text = text.replace(suffix, "")
    text = re.sub(r"[^a-z0-9à-ÿ]+", " ", text)
    return " ".join(text.split())


def normalize_catalog(value):
    if value is None:
        return ""
    return re.sub(r"[\s\-_\/\\\.]+", "", str(value).lower())


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def artist_similarity(a, b):
    a = normalize_artist(a)
    b = normalize_artist(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def label_similarity(a, b):
    a = normalize_label(a)
    b = normalize_label(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.95
    common = set(a.split()) & set(b.split())
    if common:
        return 0.85
    return SequenceMatcher(None, a, b).ratio()


def catalog_similarity(a, b):
    a = normalize_catalog(a)
    b = normalize_catalog(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    na = re.sub(r"[^0-9]", "", a)
    nb = re.sub(r"[^0-9]", "", b)
    if na and nb and na.lstrip("0") == nb.lstrip("0"):
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


# ============================================================
# DATABASE
# ============================================================

def connect_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def load_releases(conn):
    return conn.execute("""
        SELECT
            id, artist, title, label, catalog, year, genre,
            discogs, discogs_link, cover, notes, storage_code
        FROM releases
        ORDER BY id
    """).fetchall()


def load_tracks(conn):
    rows = conn.execute("""
        SELECT id, release_id, position, artist, title, duration, bpm
        FROM tracks
        ORDER BY release_id, id
    """).fetchall()
    result = {}
    for row in rows:
        result.setdefault(row["release_id"], []).append(row)
    return result


def load_local_discogs(conn):
    if not table_exists(conn, "discogs_vinyl"):
        return []
    columns = get_columns(conn, "discogs_vinyl")
    needed = [
        "id", "discogs_id", "artist", "title", "year", "catalog",
        "catalog_match", "kastcode", "instance_id", "labels",
        "catalogs", "matched_catalogs", "kastcodes"
    ]
    available = [c for c in needed if c in columns]
    if not available:
        return []
    select_sql = ", ".join(available)
    rows = conn.execute(f"SELECT {select_sql} FROM discogs_vinyl ORDER BY id").fetchall()
    return rows


def table_exists(conn, table):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def get_columns(conn, table):
    return [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def row_get(row, key, default=""):
    if row is None or key not in row.keys():
        return default
    value = row[key]
    return default if value is None else value


# ============================================================
# DISCOGS
# ============================================================

def get_token():
    token = os.environ.get("DISCOGS_TOKEN", "").strip()
    return token


def create_session(token):
    if not token:
        return None
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Authorization": f"Discogs token={token}",
    })
    return session


def verify_token(session):
    if session is None:
        return False, "Geen token"
    try:
        response = session.get(f"{DISCOGS_API}/oauth/identity", timeout=20)
    except requests.RequestException as exc:
        return False, f"Verbinding mislukt: {exc}"
    if response.status_code == 401:
        return False, "Discogs token is ongeldig."
    if response.status_code != 200:
        return False, f"Discogs HTTP {response.status_code}"
    try:
        payload = response.json()
    except Exception:
        payload = {}
    username = payload.get("username", "onbekend")
    return True, username


def split_discogs_title(value):
    text = str(value or "")
    if " - " in text:
        artist, title = text.split(" - ", 1)
        return artist.strip(), title.strip()
    return "", text.strip()


def build_search_values(release, tracks):
    artist = release["artist"] or ""
    title = release["title"] or ""
    label = release["label"] or ""
    catalog = release["catalog"] or ""
    if not title and len(tracks) == 1:
        title = tracks[0]["title"] or ""
    if not artist and len(tracks) == 1:
        artist = tracks[0]["artist"] or ""
    return artist, title, label, catalog


def live_search(session, release, tracks):
    if session is None:
        return []
    artist, title, label, catalog = build_search_values(release, tracks)
    if not title:
        return []
    queries = []
    if artist and title and catalog:
        queries.append({"artist": artist, "track": title, "catno": catalog})
    if artist and title:
        queries.append({"artist": artist, "track": title})
    if artist and title:
        queries.append({"q": f"{artist} {title}"})
    queries.append({"q": title})
    results = []
    seen = set()
    for query in queries:
        params = {
            "type": "release",
            "per_page": LIVE_RESULTS,
            "page": 1,
        }
        params.update(query)
        try:
            response = session.get(
                f"{DISCOGS_API}/database/search",
                params=params,
                timeout=30,
            )
        except requests.RequestException:
            continue
        if response.status_code == 401:
            raise RuntimeError("Discogs token is ongeldig.")
        if response.status_code == 429:
            time.sleep(10)
            continue
        if response.status_code != 200:
            continue
        try:
            payload = response.json()
        except Exception:
            continue
        for item in payload.get("results", []):
            did = item.get("id")
            if not did or did in seen:
                continue
            seen.add(did)
            results.append(item)
        time.sleep(REQUEST_DELAY)
        if len(results) >= LIVE_RESULTS:
            break
    return results


def local_to_candidate(row):
    did = str(row_get(row, "discogs_id", "") or "")
    return {
        "source": "LOCAL",
        "id": did,
        "artist": row_get(row, "artist"),
        "title": row_get(row, "title"),
        "year": row_get(row, "year"),
        "label": row_get(row, "labels"),
        "catalog": (
            row_get(row, "matched_catalogs")
            or row_get(row, "catalogs")
            or row_get(row, "catalog")
        ),
        "format": "",
        "country": "",
        "kastcodes": row_get(row, "kastcodes") or row_get(row, "kastcode"),
        "instance_id": row_get(row, "instance_id"),
        "url": f"https://www.discogs.com/release/{did}",
    }


def live_to_candidate(item):
    raw_title = item.get("title", "")
    artist, title = split_discogs_title(raw_title)
    if not artist:
        artist = str(item.get("artist", "") or "")
    labels = item.get("label", [])
    if isinstance(labels, list):
        label = " ".join(str(x) for x in labels)
    else:
        label = str(labels or "")
    catno = item.get("catno", "")
    if isinstance(catno, list):
        catno = " ".join(str(x) for x in catno)
    formats = item.get("format", [])
    if isinstance(formats, list):
        format_text = ", ".join(str(x) for x in formats)
    else:
        format_text = str(formats or "")
    did = str(item.get("id", "") or "")
    return {
        "source": "LIVE",
        "id": did,
        "artist": artist,
        "title": title,
        "year": item.get("year", "") or "",
        "label": label,
        "catalog": catno,
        "format": format_text,
        "country": item.get("country", "") or "",
        "kastcodes": "",
        "instance_id": "",
        "url": f"https://www.discogs.com/release/{did}",
    }


# ============================================================
# SCORING
# ============================================================

def score_candidate(release, candidate, tracks):
    artist, title, label, catalog = build_search_values(release, tracks)
    score = 0.0
    score += artist_similarity(artist, candidate["artist"]) * 30
    score += similarity(title, candidate["title"]) * 45
    score += label_similarity(label, candidate["label"]) * 15
    score += catalog_similarity(catalog, candidate["catalog"]) * 10

    if artist and normalize_artist(artist) == normalize_artist(candidate["artist"]):
        score += 5
    if title and normalize(title) == normalize(candidate["title"]):
        score += 7

    if catalog and candidate["catalog"]:
        a = normalize_catalog(catalog)
        b = normalize_catalog(candidate["catalog"])
        if a == b:
            score += 8
        else:
            na = re.sub(r"[^0-9]", "", a)
            nb = re.sub(r"[^0-9]", "", b)
            if na and nb and na.lstrip("0") == nb.lstrip("0"):
                score += 8

    if release["year"] and candidate["year"]:
        try:
            diff = abs(int(release["year"]) - int(candidate["year"]))
            if diff == 0:
                score += 8
            elif diff == 1:
                score += 5
            elif diff == 2:
                score += 2
            elif diff > 5:
                score -= 5
        except Exception:
            pass

    if release["storage_code"] and candidate["kastcodes"]:
        if normalize(release["storage_code"]) in normalize(candidate["kastcodes"]):
            score += 25

    fmt = normalize(candidate["format"])
    if "vinyl" in fmt:
        score += 8
    if "12" in fmt:
        score += 5
    if "promo" in fmt:
        score += 2
    if "white label" in fmt:
        score += 2
    if any(x in fmt for x in ("file", "mp3", "wav", "digital")):
        score -= 25
    if "cd" in fmt:
        score -= 18

    return round(max(score, 0.0), 2)


# ============================================================
# MAIN WINDOW
# ============================================================

class FullReviewWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kid Acid's VinylVault V3 - Full Discogs Review")
        self.resize(1600, 950)

        self.conn = connect_db()
        self.releases = load_releases(self.conn)
        self.tracks = load_tracks(self.conn)
        self.local_discogs = load_local_discogs(self.conn)

        token = get_token()
        self.session = create_session(token)
        self.token_username = ""
        self.token_ok = False
        if self.session:
            self.token_ok, self.token_username = verify_token(self.session)
            if not self.token_ok:
                self.session = None

        self.index = 0
        self.current_release = None
        self.current_tracks = []
        self.current_candidates = []
        self.current_candidate_index = 0
        self.backup_created = False

        self.reviewed = 0
        self.matched = 0
        self.kept = 0
        self.skipped = 0
        self.no_match_count = 0

        self.build_ui()
        self.load_release()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------
    def build_ui(self):
        self.setStyleSheet("""
            QWidget { background:#111111; color:#eeeeee; font-family:Arial; }
            QLineEdit, QComboBox { background:#202020; color:#eeeeee; border:1px solid #444; padding:9px; border-radius:4px; }
            QPushButton { background:#282828; color:#eeeeee; border:1px solid #444; padding:10px 18px; border-radius:4px; }
            QPushButton:hover { background:#383838; }
            QTableWidget { background:#181818; alternate-background-color:#202020; color:#eeeeee; border:1px solid #333; gridline-color:#333; selection-background-color:#444; }
            QHeaderView::section { background:#292929; color:#dddddd; padding:8px; border:0; font-weight:bold; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)

        top = QHBoxLayout()
        brand = QLabel("KID ACID'S")
        brand.setStyleSheet("font-size:24px;font-weight:bold;")
        top.addWidget(brand)
        sub = QLabel("VINYL VAULT")
        sub.setStyleSheet("font-size:22px;font-weight:bold;color:#bbbbbb;")
        top.addWidget(sub)
        top.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Zoek artiest, titel, label, catalogus, storage of ID...")
        self.search_box.textChanged.connect(self.search_collection)
        top.addWidget(self.search_box, 1)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Alle 5583",
            "Zonder Discogs-ID",
            "Met Discogs-ID",
        ])
        self.filter_combo.currentIndexChanged.connect(self.search_collection)
        top.addWidget(self.filter_combo)
        root.addLayout(top)

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("background:#1b1b1b;padding:10px;color:#bbbbbb;")
        root.addWidget(self.stats_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        # LEFT
        left = QFrame()
        left_layout = QVBoxLayout(left)
        label = QLabel("COLLECTIE")
        label.setStyleSheet("font-size:18px;font-weight:bold;")
        left_layout.addWidget(label)

        self.collection_table = QTableWidget()
        self.collection_table.setColumnCount(5)
        self.collection_table.setHorizontalHeaderLabels(["ID", "Artist", "Titel", "Label", "Discogs"])
        self.collection_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.collection_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.collection_table.cellClicked.connect(self.select_release_from_table)
        left_layout.addWidget(self.collection_table)
        splitter.addWidget(left)

        # CENTER
        center = QFrame()
        center_layout = QVBoxLayout(center)
        title = QLabel("VINYLVAULT RELEASE")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        center_layout.addWidget(title)

        self.release_card = QLabel("")
        self.release_card.setWordWrap(True)
        self.release_card.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.release_card.setStyleSheet("background:#191919;border:1px solid #333;padding:18px;font-size:15px;")
        center_layout.addWidget(self.release_card, 1)

        track_title = QLabel("TRACKLIST")
        track_title.setStyleSheet("font-size:16px;font-weight:bold;")
        center_layout.addWidget(track_title)

        self.track_table = QTableWidget()
        self.track_table.setColumnCount(4)
        self.track_table.setHorizontalHeaderLabels(["Pos", "Artist", "Titel", "BPM"])
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        center_layout.addWidget(self.track_table, 1)
        splitter.addWidget(center)

        # RIGHT
        right = QFrame()
        right_layout = QVBoxLayout(right)
        candidate_title = QLabel("DISCOGS VERSIES")
        candidate_title.setStyleSheet("font-size:18px;font-weight:bold;")
        right_layout.addWidget(candidate_title)

        self.candidate_table = QTableWidget()
        self.candidate_table.setColumnCount(6)
        self.candidate_table.setHorizontalHeaderLabels(["Score", "Bron", "Discogs", "Artist", "Titel", "Label"])
        self.candidate_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.candidate_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.candidate_table.cellClicked.connect(self.select_candidate)
        right_layout.addWidget(self.candidate_table, 1)

        self.candidate_card = QLabel("")
        self.candidate_card.setWordWrap(True)
        self.candidate_card.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.candidate_card.setOpenExternalLinks(True)
        self.candidate_card.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.candidate_card.setStyleSheet("background:#191919;border:1px solid #333;padding:15px;font-size:14px;")
        right_layout.addWidget(self.candidate_card, 1)
        splitter.addWidget(right)
        splitter.setSizes([430, 560, 610])

        buttons = QHBoxLayout()

        self.keep_button = QPushButton("✓ BEHOUD HUIDIGE")
        self.keep_button.clicked.connect(self.keep_current)
        buttons.addWidget(self.keep_button)

        self.accept_button = QPushButton("✓ KIES DEZE DISCOGS")
        self.accept_button.setStyleSheet("background:#294d2d;font-weight:bold;font-size:16px;")
        self.accept_button.clicked.connect(self.accept_candidate)
        buttons.addWidget(self.accept_button)

        self.reject_button = QPushButton("✗ NIET DEZE")
        self.reject_button.clicked.connect(self.reject_candidate)
        buttons.addWidget(self.reject_button)

        self.no_match_button = QPushButton("Ø GEEN VAN DEZE")
        self.no_match_button.clicked.connect(self.no_match)
        buttons.addWidget(self.no_match_button)

        self.next_release_button = QPushButton("→ VOLGENDE VINYL")
        self.next_release_button.clicked.connect(self.next_release)
        buttons.addWidget(self.next_release_button)

        self.stop_button = QPushButton("STOP")
        self.stop_button.clicked.connect(self.close)
        buttons.addWidget(self.stop_button)

        root.addLayout(buttons)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color:#aaaaaa;padding-top:5px;")
        root.addWidget(self.status_label)

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------
    def update_stats(self):
        total = len(self.releases)
        with_discogs = sum(1 for r in self.releases if r["discogs"] and str(r["discogs"]).strip())
        without_discogs = total - with_discogs
        live = f"LIVE: {self.token_username}" if self.token_ok else "LIVE: UIT"
        self.stats_label.setText(
            f"COLLECTIE {total}   |   MET DISCOGS {with_discogs}   |   ZONDER DISCOGS {without_discogs}   |   "
            f"GEREVIEWD {self.reviewed}   |   GEKOPPELD {self.matched}   |   BEHOUDEN {self.kept}   |   {live}"
        )

    # --------------------------------------------------------
    # COLLECTION SEARCH
    # --------------------------------------------------------
    def search_collection(self):
        text = normalize(self.search_box.text())
        mode = self.filter_combo.currentIndex()
        self.collection_table.setRowCount(0)
        shown = 0
        for row in self.releases:
            has_id = bool(row["discogs"] and str(row["discogs"]).strip())
            if mode == 1 and has_id:
                continue
            if mode == 2 and not has_id:
                continue
            haystack = normalize(" ".join([
                str(row["id"] or ""), str(row["artist"] or ""), str(row["title"] or ""),
                str(row["label"] or ""), str(row["catalog"] or ""),
                str(row["storage_code"] or ""), str(row["discogs"] or ""),
            ]))
            if text and text not in haystack:
                continue
            self.collection_table.insertRow(shown)
            values = [row["id"], row["artist"] or "", row["title"] or "", row["label"] or "", row["discogs"] or "-"]
            for col, value in enumerate(values):
                self.collection_table.setItem(shown, col, QTableWidgetItem(str(value)))
            shown += 1
            if shown >= 1000:
                break
        self.collection_table.resizeColumnsToContents()

    # --------------------------------------------------------
    # LOAD CURRENT RELEASE
    # --------------------------------------------------------
    def load_release(self):
        self.update_stats()
        self.search_collection()
        if self.index >= len(self.releases):
            self.finish()
            return

        release = self.releases[self.index]
        self.current_release = release
        self.current_tracks = self.tracks.get(release["id"], [])
        self.display_release(release)
        self.display_tracks(self.current_tracks)

        local = self.find_local_candidates(release, self.current_tracks)
        live = []

        should_live_search = self.session is not None and (
            not local or local[0]["score"] < 75
        )

        if should_live_search:
            self.status_label.setText("Live Discogs zoeken...")
            QApplication.processEvents()
            try:
                live = live_search(self.session, release, self.current_tracks)
            except RuntimeError as exc:
                self.token_ok = False
                self.session = None
                QMessageBox.warning(self, "Discogs", str(exc))
            except Exception as exc:
                self.status_label.setText(f"Live zoeken mislukt: {exc}")

        combined = []
        seen = set()

        current_id = str(release["discogs"] or "")

        # Current first
        if current_id:
            for item in local:
                if str(item["data"]["id"]) == current_id:
                    item["current"] = True
                    combined.append(item)
                    seen.add(current_id)
                    break

        for item in local:
            did = str(item["data"]["id"])
            if did in seen:
                continue
            item["current"] = False
            combined.append(item)
            seen.add(did)

        for raw in live:
            candidate = live_to_candidate(raw)
            did = candidate["id"]
            if not did or did in seen:
                continue
            score = score_candidate(release, candidate, self.current_tracks)
            combined.append({
                "score": score,
                "data": candidate,
                "source": "LIVE",
                "current": did == current_id,
            })
            seen.add(did)

        # Put current first, then best score.
        combined.sort(key=lambda x: (0 if x.get("current") else 1, -x["score"]))
        self.current_candidates = combined[:MAX_CANDIDATES]
        self.current_candidate_index = 0
        self.populate_candidate_table()

        if self.current_candidates:
            self.show_candidate()
        else:
            self.candidate_card.setText("<h2>GEEN KANDIDATEN</h2><p>Geen lokale of live Discogs-kandidaten gevonden.</p>")
            self.disable_actions(no_current=not bool(release["discogs"]))

    # --------------------------------------------------------
    # LOCAL CANDIDATES
    # --------------------------------------------------------
    def find_local_candidates(self, release, tracks):
        candidates = []
        seen = set()
        for row in self.local_discogs:
            candidate = local_to_candidate(row)
            did = candidate["id"]
            if not did or did in seen:
                continue
            seen.add(did)
            score = score_candidate(release, candidate, tracks)
            if score >= 30:
                candidates.append({
                    "score": score,
                    "data": candidate,
                    "source": "LOCAL",
                    "current": False,
                })
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:LOCAL_RESULTS]

    # --------------------------------------------------------
    # DISPLAY RELEASE
    # --------------------------------------------------------
    def display_release(self, release):
        current_id = str(release["discogs"] or "-")
        link = release["discogs_link"] or ""
        html = f"""
        <h1>{release['artist'] or '-'}</h1>
        <h2>{release['title'] or '-'}</h2>
        <p><b>Status:</b> {'HEEFT DISCOGS-ID' if release['discogs'] else 'GEEN DISCOGS-ID'}</p>
        <p><b>Vault ID:</b> {release['id']}</p>
        <p><b>Label:</b> {release['label'] or '-'}</p>
        <p><b>Catalog:</b> {release['catalog'] or '-'}</p>
        <p><b>Year:</b> {release['year'] or '-'}</p>
        <p><b>Storage:</b> {release['storage_code'] or '-'}</p>
        <p><b>Genre:</b> {release['genre'] or '-'}</p>
        <hr>
        <p><b>Huidige Discogs-ID:</b> {current_id}</p>
        """
        if link:
            html += f'<p><b>Huidige link:</b><br><a href="{link}">{link}</a></p>'
        self.release_card.setText(html)

    # --------------------------------------------------------
    # DISPLAY TRACKS
    # --------------------------------------------------------
    def display_tracks(self, tracks):
        self.track_table.setRowCount(0)
        for r, track in enumerate(tracks):
            self.track_table.insertRow(r)
            values = [track["position"] or "", track["artist"] or "", track["title"] or "", track["bpm"] or ""]
            for c, value in enumerate(values):
                self.track_table.setItem(r, c, QTableWidgetItem(str(value)))
        self.track_table.resizeColumnsToContents()

    # --------------------------------------------------------
    # CANDIDATE TABLE
    # --------------------------------------------------------
    def populate_candidate_table(self):
        self.candidate_table.setRowCount(0)
        for r, candidate in enumerate(self.current_candidates):
            self.candidate_table.insertRow(r)
            data = candidate["data"]
            source = "HUIDIG" if candidate.get("current") else candidate["source"]
            values = [
                f"{candidate['score']:.1f}", source, data["id"], data["artist"], data["title"], data["label"]
            ]
            for c, value in enumerate(values):
                self.candidate_table.setItem(r, c, QTableWidgetItem(str(value or "")))
        self.candidate_table.resizeColumnsToContents()
        if self.current_candidates:
            self.candidate_table.selectRow(self.current_candidate_index)

    # --------------------------------------------------------
    # SHOW CANDIDATE
    # --------------------------------------------------------
    def show_candidate(self):
        if not self.current_candidates:
            return
        candidate = self.current_candidates[self.current_candidate_index]
        data = candidate["data"]
        current = candidate.get("current", False)
        current_id = str(self.current_release["discogs"] or "")

        html = f"""
        <h2>{data['artist'] or '-'}</h2>
        <h3>{data['title'] or '-'}</h3>
        <p><b>Score:</b> {candidate['score']:.2f}</p>
        <p><b>Bron:</b> {'HUIDIGE KOPPELING' if current else candidate['source']}</p>
        <p><b>Discogs ID:</b> {data['id'] or '-'}</p>
        <p><b>Label:</b> {data['label'] or '-'}</p>
        <p><b>Catalog:</b> {data['catalog'] or '-'}</p>
        <p><b>Year:</b> {data['year'] or '-'}</p>
        <p><b>Country:</b> {data['country'] or '-'}</p>
        <p><b>Format:</b> {data['format'] or '-'}</p>
        """
        if data["kastcodes"]:
            html += f"<p><b>Kastcode:</b> {data['kastcodes']}</p>"
        if current_id and not current:
            html += f"<p><b>Huidige ID:</b> {current_id}</p>"
        html += f'<hr><p><b>Discogs:</b><br><a href="{data["url"]}">{data["url"]}</a></p>'
        self.candidate_card.setText(html)
        self.candidate_table.selectRow(self.current_candidate_index)
        self.enable_actions()
        self.status_label.setText(
            f"Kandidaat {self.current_candidate_index + 1}/{len(self.current_candidates)}"
        )

    # --------------------------------------------------------
    # SELECTION
    # --------------------------------------------------------
    def select_release_from_table(self, row, column):
        item = self.collection_table.item(row, 0)
        if item is None:
            return
        try:
            release_id = int(item.text())
        except ValueError:
            return
        for idx, release in enumerate(self.releases):
            if release["id"] == release_id:
                self.index = idx
                self.load_release()
                return

    def select_candidate(self, row, column):
        if 0 <= row < len(self.current_candidates):
            self.current_candidate_index = row
            self.show_candidate()

    # --------------------------------------------------------
    # ACTION BUTTONS
    # --------------------------------------------------------
    def enable_actions(self):
        self.keep_button.setEnabled(bool(self.current_release and self.current_release["discogs"]))
        self.accept_button.setEnabled(True)
        self.reject_button.setEnabled(len(self.current_candidates) > 1)
        self.no_match_button.setEnabled(True)

    def disable_actions(self, no_current=False):
        self.keep_button.setEnabled(bool(self.current_release and self.current_release["discogs"]))
        self.accept_button.setEnabled(False)
        self.reject_button.setEnabled(False)
        self.no_match_button.setEnabled(True)

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------
    def create_backup(self):
        if self.backup_created:
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(
            os.path.dirname(DB),
            f"vinylvault_BEFORE_FULL_REVIEW_{stamp}.db",
        )
        shutil.copy2(DB, backup)
        self.backup_created = True
        QMessageBox.information(
            self,
            "Database backup",
            f"Backup gemaakt vóór de eerste wijziging:\n\n{backup}",
        )

    # --------------------------------------------------------
    # ACCEPT
    # --------------------------------------------------------
    def accept_candidate(self):
        if not self.current_candidates:
            return
        candidate = self.current_candidates[self.current_candidate_index]
        data = candidate["data"]
        release = self.current_release
        if not data["id"]:
            return

        if release["discogs"] and str(release["discogs"]) == str(data["id"]):
            self.keep_current()
            return

        answer = QMessageBox.question(
            self,
            "Discogs koppelen",
            (
                "Deze Discogs-release koppelen?\n\n"
                f"VINYLVAULT:\n{release['artist'] or '-'} - {release['title'] or '-'}\n"
                f"Label: {release['label'] or '-'}\nCatalog: {release['catalog'] or '-'}\n\n"
                f"DISCOGS:\n{data['artist'] or '-'} - {data['title'] or '-'}\n"
                f"Label: {data['label'] or '-'}\nCatalog: {data['catalog'] or '-'}\n\n"
                f"Discogs ID: {data['id']}\nScore: {candidate['score']:.2f}"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.create_backup()
        except Exception as exc:
            QMessageBox.critical(self, "Backup fout", str(exc))
            return

        link = f"https://www.discogs.com/release/{data['id']}"
        try:
            self.conn.execute(
                "UPDATE releases SET discogs=?, discogs_link=? WHERE id=?",
                (str(data["id"]), link, release["id"]),
            )
            self.conn.commit()
        except Exception as exc:
            self.conn.rollback()
            QMessageBox.critical(self, "Database fout", str(exc))
            return

        # refresh in-memory release
        self.releases = load_releases(self.conn)
        self.matched += 1
        self.reviewed += 1
        self.index = min(self.index + 1, len(self.releases))
        self.load_release()

    # --------------------------------------------------------
    # KEEP CURRENT
    # --------------------------------------------------------
    def keep_current(self):
        if not self.current_release or not self.current_release["discogs"]:
            return
        self.kept += 1
        self.reviewed += 1
        self.index += 1
        self.load_release()

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------
    def reject_candidate(self):
        if not self.current_candidates:
            return
        if self.current_candidate_index + 1 >= len(self.current_candidates):
            self.candidate_card.setText("<h2>GEEN KANDIDAAT MEER</h2><p>Alle kandidaten zijn afgewezen.</p>")
            self.accept_button.setEnabled(False)
            self.reject_button.setEnabled(False)
            return
        self.current_candidate_index += 1
        self.show_candidate()

    # --------------------------------------------------------
    # NO MATCH
    # --------------------------------------------------------
    def no_match(self):
        self.no_match_count += 1
        self.reviewed += 1
        self.index += 1
        self.load_release()

    # --------------------------------------------------------
    # NEXT
    # --------------------------------------------------------
    def next_release(self):
        self.skipped += 1
        self.index += 1
        self.load_release()

    # --------------------------------------------------------
    # FINISH
    # --------------------------------------------------------
    def finish(self):
        QMessageBox.information(
            self,
            "Review klaar",
            (
                "Volledige collectie-review klaar.\n\n"
                f"Gereviewd: {self.reviewed}\n"
                f"Nieuwe koppelingen: {self.matched}\n"
                f"Huidige behouden: {self.kept}\n"
                f"Geen match: {self.no_match_count}\n"
                f"Overgeslagen: {self.skipped}"
            ),
        )
        self.close()

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------
    def closeEvent(self, event):
        try:
            self.conn.close()
        except Exception:
            pass
        event.accept()


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("FULL COLLECTION DISCOGS REVIEW")
    print("=" * 80)
    print()
    print("Database:")
    print(DB)

    token = get_token()
    if token:
        print("Discogs token gevonden.")
    else:
        print("Discogs token NIET GEVONDEN.")
        print("Lokale Discogs-data blijft beschikbaar.")

    app = QApplication(sys.argv)
    app.setApplicationName("Kid Acid's VinylVault V3")

    window = FullReviewWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
