# ============================================================
# KID ACID'S VINYLVAULT V3
# FULL COLLECTION DISCOGS REVIEWER
# ============================================================
#
# ALLE 5583 VINYLVAULT RELEASES
#
# Bestaande Discogs-ID's:
#   -> worden gecontroleerd
#
# Geen Discogs-ID:
#   -> wordt gezocht
#
# BRONNEN:
#   1. lokale discogs_vinyl
#   2. live Discogs API
#
# BELANGRIJK:
#   - bestaande Discogs-ID wordt NOOIT automatisch vervangen
#   - alleen JA van gebruiker kan een wijziging maken
#   - bij bestaande koppeling kun je:
#         BEHOUD HUIDIGE
#         KIES KANDIDAAT
#         GEEN VAN DEZE
#
# DATABASE:
#   alleen releases.discogs
#   en releases.discogs_link
#   worden gewijzigd
#
# ============================================================

import os
import re
import sys
import shutil
import sqlite3

from datetime import datetime
from difflib import SequenceMatcher

import requests

from PySide6.QtCore import (
    Qt,
    Signal
)

from PySide6.QtGui import (
    QFont
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QSplitter,
    QLineEdit,
    QComboBox,
    QScrollArea,
    QSizePolicy,
    QHeaderView
)


# ============================================================
# CONFIG
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DISCOGS_API = (
    "https://api.discogs.com"
)

USER_AGENT = (
    "KidAcidVinylVaultV3/1.0 "
    "(Full Collection Review)"
)

REQUEST_DELAY = 1.1

LIVE_RESULTS = 30

MAX_CANDIDATES = 12


# ============================================================
# DATABASE PATH
# ============================================================

def find_database():

    paths = [
        os.path.join(
            SCRIPT_DIR,
            "data",
            "vinylvault.db"
        ),
        os.path.join(
            os.path.dirname(SCRIPT_DIR),
            "data",
            "vinylvault.db"
        ),
        os.path.join(
            os.path.dirname(
                os.path.dirname(SCRIPT_DIR)
            ),
            "data",
            "vinylvault.db"
        )
    ]

    for path in paths:

        path = os.path.abspath(path)

        if os.path.exists(path):

            return path

    raise FileNotFoundError(
        "vinylvault.db niet gevonden."
    )


DB = find_database()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(value):

    if value is None:
        return ""

    text = str(value).lower().strip()

    text = text.replace(
        "&",
        " and "
    )

    text = text.replace(
        "’",
        "'"
    )

    text = text.replace(
        "`",
        "'"
    )

    text = re.sub(
        r"[^a-z0-9à-ÿ]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_artist(value):

    if value is None:
        return ""

    text = str(value).lower()

    text = text.replace(
        "&",
        " and "
    )

    text = re.sub(
        r"\bfeaturing\b",
        " feat ",
        text
    )

    text = re.sub(
        r"\bfeat\.?\b",
        " feat ",
        text
    )

    text = re.sub(
        r"[^a-z0-9à-ÿ]+",
        " ",
        text
    )

    return " ".join(
        text.split()
    )


def normalize_label(value):

    if value is None:
        return ""

    text = str(value).lower()

    text = text.replace(
        "&",
        " and "
    )

    for token in [
        " records",
        " recordings",
        " record",
        " music",
        " label",
        " ltd",
        " limited",
        " inc",
        " bv",
        " b.v."
    ]:

        text = text.replace(
            token,
            ""
        )

    text = re.sub(
        r"[^a-z0-9à-ÿ]+",
        " ",
        text
    )

    return " ".join(
        text.split()
    )


def normalize_catalog(value):

    if value is None:
        return ""

    text = str(value).lower()

    text = re.sub(
        r"[\s\-_\/\\\.]+",
        "",
        text
    )

    return text


# ============================================================
# SIMILARITY
# ============================================================

def similarity(a, b):

    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def artist_similarity(a, b):

    a = normalize_artist(a)
    b = normalize_artist(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def label_similarity(a, b):

    a = normalize_label(a)
    b = normalize_label(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    if a in b or b in a:
        return 0.95

    common = (
        set(a.split())
        &
        set(b.split())
    )

    if common:
        return 0.85

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def catalog_similarity(a, b):

    a = normalize_catalog(a)
    b = normalize_catalog(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    na = re.sub(
        r"[^0-9]",
        "",
        a
    )

    nb = re.sub(
        r"[^0-9]",
        "",
        b
    )

    if (
        na
        and nb
        and na.lstrip("0")
        == nb.lstrip("0")
    ):
        return 1.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


# ============================================================
# DATABASE
# ============================================================

def connect():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATA LOAD
# ============================================================

def load_tracks(conn):

    rows = conn.execute(
        """
        SELECT
            release_id,
            position,
            artist,
            title,
            duration,
            bpm
        FROM tracks
        ORDER BY release_id, id
        """
    ).fetchall()

    result = {}

    for row in rows:

        result.setdefault(
            row["release_id"],
            []
        ).append(row)

    return result


def load_releases(conn):

    return conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            label,
            catalog,
            year,
            genre,
            discogs,
            discogs_link,
            cover,
            notes,
            storage_code
        FROM releases
        ORDER BY id
        """
    ).fetchall()


def load_local_discogs(conn):

    rows = conn.execute(
        """
        SELECT
            id,
            discogs_id,
            artist,
            title,
            year,
            catalog,
            catalog_match,
            kastcode,
            instance_id,
            labels,
            catalogs,
            matched_catalogs,
            kastcodes
        FROM discogs_vinyl
        ORDER BY id
        """
    ).fetchall()

    return rows


# ============================================================
# TOKEN
# ============================================================

def get_token():

    return (
        os.environ.get(
            "DISCOGS_TOKEN",
            ""
        ).strip()
    )


# ============================================================
# DISCogs SESSION
# ============================================================

def create_session(token):

    if not token:
        return None

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Authorization":
                f"Discogs token={token}"
        }
    )

    return session


# ============================================================
# TRACK SEARCH TEXT
# ============================================================

def get_search_values(
    release,
    tracks
):

    artist = (
        release["artist"]
        or ""
    )

    title = (
        release["title"]
        or ""
    )

    label = (
        release["label"]
        or ""
    )

    catalog = (
        release["catalog"]
        or ""
    )

    # Veel oude releases hebben een lege release-title.
    # Gebruik dan de enige track als zoekterm.
    if (
        not title
        and tracks
    ):

        if len(tracks) == 1:

            title = (
                tracks[0]["title"]
                or ""
            )

            if (
                not artist
                and tracks[0]["artist"]
            ):

                artist = (
                    tracks[0]["artist"]
                )

    return (
        artist,
        title,
        label,
        catalog
    )


# ============================================================
# SPLIT DISCOGS TITLE
# ============================================================

def split_discogs_title(value):

    value = str(
        value or ""
    )

    if " - " in value:

        artist, title = (
            value.split(
                " - ",
                1
            )
        )

        return (
            artist.strip(),
            title.strip()
        )

    return (
        "",
        value.strip()
    )


# ============================================================
# LIVE SEARCH
# ============================================================

def live_search(
    session,
    release,
    tracks
):

    if session is None:
        return []

    artist, title, label, catalog = (
        get_search_values(
            release,
            tracks
        )
    )

    if not title:
        return []

    queries = []

    if (
        artist
        and title
        and catalog
    ):

        queries.append(
            {
                "type": "release",
                "artist": artist,
                "track": title,
                "catno": catalog,
                "per_page": LIVE_RESULTS,
                "page": 1
            }
        )

    if (
        artist
        and title
    ):

        queries.append(
            {
                "type": "release",
                "artist": artist,
                "track": title,
                "per_page": LIVE_RESULTS,
                "page": 1
            }
        )

    queries.append(
        {
            "type": "release",
            "q": f"{artist} {title}",
            "per_page": LIVE_RESULTS,
            "page": 1
        }
    )

    queries.append(
        {
            "type": "release",
            "q": title,
            "per_page": LIVE_RESULTS,
            "page": 1
        }
    )

    results = []

    seen = set()

    for params in queries:

        try:

            response = session.get(
                f"{DISCOGS_API}/database/search",
                params=params,
                timeout=30
            )

        except requests.RequestException:

            continue

        if response.status_code == 401:

            raise RuntimeError(
                "Discogs token is ongeldig."
            )

        if response.status_code == 429:

            import time

            time.sleep(10)

            continue

        if response.status_code != 200:

            continue

        try:

            payload = response.json()

        except Exception:

            continue

        for item in payload.get(
            "results",
            []
        ):

            discogs_id = item.get(
                "id"
            )

            if not discogs_id:
                continue

            if discogs_id in seen:
                continue

            seen.add(
                discogs_id
            )

            results.append(
                item
            )

        import time

        time.sleep(
            REQUEST_DELAY
        )

        if len(results) >= 30:
            break

    return results


# ============================================================
# LOCAL CANDIDATE
# ============================================================

def local_candidate(row):

    return {
        "source": "LOCAL",
        "id": str(
            row["discogs_id"]
            or ""
        ),
        "artist":
            row["artist"] or "",
        "title":
            row["title"] or "",
        "year":
            row["year"] or "",
        "label":
            row["labels"] or "",
        "catalog":
            (
                row["matched_catalogs"]
                or row["catalogs"]
                or row["catalog"]
                or ""
            ),
        "format": "",
        "country": "",
        "kastcodes":
            (
                row["kastcodes"]
                or row["kastcode"]
                or ""
            ),
        "instance_id":
            row["instance_id"]
            or "",
        "url":
            (
                "https://www.discogs.com/release/"
                f"{row['discogs_id']}"
            )
    }


# ============================================================
# LIVE CANDIDATE
# ============================================================

def live_candidate(item):

    raw_title = item.get(
        "title",
        ""
    )

    artist, title = split_discogs_title(
        raw_title
    )

    if not artist:

        artist = str(
            item.get(
                "artist",
                ""
            )
        )

    labels = item.get(
        "label",
        []
    )

    if isinstance(
        labels,
        list
    ):

        label = " ".join(
            str(x)
            for x in labels
        )

    else:

        label = str(
            labels or ""
        )

    catno = item.get(
        "catno",
        ""
    )

    if isinstance(
        catno,
        list
    ):

        catno = " ".join(
            str(x)
            for x in catno
        )

    formats = item.get(
        "format",
        []
    )

    if isinstance(
        formats,
        list
    ):

        format_text = ", ".join(
            str(x)
            for x in formats
        )

    else:

        format_text = str(
            formats or ""
        )

    discogs_id = item.get(
        "id",
        ""
    )

    return {
        "source": "LIVE",
        "id":
            str(discogs_id),
        "artist":
            artist,
        "title":
            title,
        "year":
            item.get(
                "year",
                ""
            ),
        "label":
            label,
        "catalog":
            catno,
        "format":
            format_text,
        "country":
            item.get(
                "country",
                ""
            ),
        "kastcodes":
            "",
        "instance_id":
            "",
        "url":
            (
                "https://www.discogs.com/release/"
                f"{discogs_id}"
            )
    }


# ============================================================
# SCORE
# ============================================================

def score_candidate(
    release,
    candidate,
    tracks
):

    artist, title, label, catalog = (
        get_search_values(
            release,
            tracks
        )
    )

    if not artist and tracks:

        artist = (
            tracks[0]["artist"]
            or ""
        )

    if not title and tracks:

        title = (
            tracks[0]["title"]
            or ""
        )

    score = 0.0

    artist_score = artist_similarity(
        artist,
        candidate["artist"]
    )

    title_score = similarity(
        title,
        candidate["title"]
    )

    label_score = label_similarity(
        label,
        candidate["label"]
    )

    catalog_score = catalog_similarity(
        catalog,
        candidate["catalog"]
    )

    score += (
        artist_score
        * 30
    )

    score += (
        title_score
        * 45
    )

    score += (
        label_score
        * 15
    )

    score += (
        catalog_score
        * 10
    )

    # Exact artist
    if (
        normalize_artist(artist)
        ==
        normalize_artist(
            candidate["artist"]
        )
        and artist
    ):

        score += 5

    # Exact title
    if (
        normalize(title)
        ==
        normalize(
            candidate["title"]
        )
        and title
    ):

        score += 7

    # Catalog exact / numeric
    if (
        catalog
        and candidate["catalog"]
    ):

        a = normalize_catalog(
            catalog
        )

        b = normalize_catalog(
            candidate["catalog"]
        )

        if a == b:

            score += 8

        else:

            na = re.sub(
                r"[^0-9]",
                "",
                a
            )

            nb = re.sub(
                r"[^0-9]",
                "",
                b
            )

            if (
                na
                and nb
                and na.lstrip("0")
                ==
                nb.lstrip("0")
            ):

                score += 8

    # Year
    if (
        release["year"]
        and candidate["year"]
    ):

        try:

            difference = abs(
                int(release["year"])
                -
                int(candidate["year"])
            )

            if difference == 0:
                score += 8

            elif difference == 1:
                score += 5

            elif difference == 2:
                score += 2

            elif difference > 5:
                score -= 5

        except Exception:
            pass

    # Local storage / kastcode
    if (
        release["storage_code"]
        and candidate["kastcodes"]
    ):

        if normalize(
            release["storage_code"]
        ) in normalize(
            candidate["kastcodes"]
        ):

            score += 25

    # Format
    fmt = normalize(
        candidate["format"]
    )

    if "vinyl" in fmt:
        score += 8

    if "12" in fmt:
        score += 5

    if "promo" in fmt:
        score += 2

    if "white label" in fmt:
        score += 2

    if (
        "file" in fmt
        or "mp3" in fmt
        or "wav" in fmt
        or "digital" in fmt
    ):

        score -= 25

    if "cd" in fmt:
        score -= 18

    return round(
        max(
            score,
            0
        ),
        2
    )


# ============================================================
# STATUS
# ============================================================

def compare_status(
    current_score,
    best_score,
    second_score
):

    if current_score <= 0:

        return "GEEN MATCH"

    if (
        current_score >= 85
        and (
            second_score <= 0
            or current_score - second_score >= 5
        )
    ):

        return "STERK"

    if current_score >= 65:

        return "CONTROLEREN"

    return "ZWAK"


# ============================================================
# UI
# ============================================================

class FullReviewWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Kid Acid's VinylVault V3"
        )

        self.resize(
            1600,
            950
        )

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        self.conn = connect()

        self.tracks = load_tracks(
            self.conn
        )

        self.releases = load_releases(
            self.conn
        )

        self.local_discogs = (
            load_local_discogs(
                self.conn
            )
        )

        # ----------------------------------------------------
        # DISCOGS
        # ----------------------------------------------------

        token = get_token()

        self.session = create_session(
            token
        )

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.index = 0

        self.current_candidates = []

        self.current_candidate_index = 0

        self.backup_created = False

        self.reviewed = 0

        self.matched = 0

        self.kept_current = 0

        self.skipped = 0

        self.needs_review = 0

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.build_ui()

        self.load_release()


    # ========================================================
    # STYLE
    # ========================================================

    def build_ui(self):

        self.setStyleSheet(
            """
            QWidget {
                background: #111111;
                color: #eeeeee;
                font-family: Arial;
            }

            QLineEdit,
            QComboBox {
                background: #202020;
                color: #eeeeee;
                border: 1px solid #444444;
                padding: 9px;
                border-radius: 4px;
            }

            QPushButton {
                background: #282828;
                color: #eeeeee;
                border: 1px solid #444444;
                padding: 10px 18px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background: #383838;
            }

            QTableWidget {
                background: #181818;
                alternate-background-color: #202020;
                color: #eeeeee;
                border: 1px solid #333333;
                gridline-color: #333333;
                selection-background-color: #444444;
            }

            QHeaderView::section {
                background: #292929;
                color: #dddddd;
                padding: 8px;
                border: 0;
                font-weight: bold;
            }

            QScrollArea {
                border: none;
            }
            """
        )

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            14,
            14,
            14,
            14
        )

        # ====================================================
        # TOP BAR
        # ====================================================

        top = QHBoxLayout()

        brand = QLabel(
            "KID ACID'S"
        )

        brand.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        top.addWidget(
            brand
        )

        vault = QLabel(
            "VINYL VAULT"
        )

        vault.setStyleSheet(
            """
            QLabel {
                color: #bbbbbb;
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        top.addWidget(
            vault
        )

        top.addStretch()

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(
            "Zoek artiest, titel, label, catalogus of ID..."
        )

        self.search_box.textChanged.connect(
            self.search_collection
        )

        top.addWidget(
            self.search_box
        )

        self.filter_combo = QComboBox()

        self.filter_combo.addItems(
            [
                "Alle 5583",
                "Zonder Discogs-ID",
                "Met Discogs-ID",
                "Controleren"
            ]
        )

        self.filter_combo.currentIndexChanged.connect(
            self.search_collection
        )

        top.addWidget(
            self.filter_combo
        )

        root.addLayout(
            top
        )

        # ====================================================
        # INFO BAR
        # ====================================================

        self.stats_label = QLabel(
            ""
        )

        self.stats_label.setStyleSheet(
            """
            QLabel {
                background: #1b1b1b;
                padding: 10px;
                color: #bbbbbb;
            }
            """
        )

        root.addWidget(
            self.stats_label
        )

        # ====================================================
        # MAIN SPLITTER
        # ====================================================

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        root.addWidget(
            splitter,
            1
        )

        # ====================================================
        # LEFT COLLECTION
        # ====================================================

        left = QFrame()

        left_layout = QVBoxLayout(
            left
        )

        left_title = QLabel(
            "COLLECTIE"
        )

        left_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        left_layout.addWidget(
            left_title
        )

        self.collection_table = (
            QTableWidget()
        )

        self.collection_table.setColumnCount(
            5
        )

        self.collection_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Artist",
                "Titel",
                "Label",
                "Discogs"
            ]
        )

        self.collection_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.collection_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.collection_table.cellClicked.connect(
            self.select_release_from_table
        )

        self.collection_table.horizontalHeader().setStretchLastSection(
            True
        )

        left_layout.addWidget(
            self.collection_table
        )

        splitter.addWidget(
            left
        )

        # ====================================================
        # CENTER
        # ====================================================

        center = QFrame()

        center_layout = QVBoxLayout(
            center
        )

        current_title = QLabel(
            "VINYLVAULT RELEASE"
        )

        current_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        center_layout.addWidget(
            current_title
        )

        self.release_card = QLabel(
            ""
        )

        self.release_card.setWordWrap(
            True
        )

        self.release_card.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.release_card.setStyleSheet(
            """
            QLabel {
                background: #191919;
                border: 1px solid #333333;
                padding: 18px;
                font-size: 15px;
            }
            """
        )

        center_layout.addWidget(
            self.release_card,
            1
        )

        tracks_title = QLabel(
            "TRACKLIST"
        )

        tracks_title.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            """
        )

        center_layout.addWidget(
            tracks_title
        )

        self.track_table = QTableWidget()

        self.track_table.setColumnCount(
            4
        )

        self.track_table.setHorizontalHeaderLabels(
            [
                "Pos",
                "Artist",
                "Titel",
                "BPM"
            ]
        )

        self.track_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        center_layout.addWidget(
            self.track_table,
            1
        )

        splitter.addWidget(
            center
        )

        # ====================================================
        # RIGHT
        # ====================================================

        right = QFrame()

        right_layout = QVBoxLayout(
            right
        )

        candidate_title = QLabel(
            "DISCOGS VERSIES"
        )

        candidate_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        right_layout.addWidget(
            candidate_title
        )

        self.candidate_table = (
            QTableWidget()
        )

        self.candidate_table.setColumnCount(
            6
        )

        self.candidate_table.setHorizontalHeaderLabels(
            [
                "Score",
                "Bron",
                "Discogs",
                "Artist",
                "Titel",
                "Label"
            ]
        )

        self.candidate_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.candidate_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.candidate_table.cellClicked.connect(
            self.select_candidate
        )

        right_layout.addWidget(
            self.candidate_table,
            1
        )

        self.candidate_card = QLabel(
            ""
        )

        self.candidate_card.setWordWrap(
            True
        )

        self.candidate_card.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        self.candidate_card.setOpenExternalLinks(
            True
        )

        self.candidate_card.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )

        self.candidate_card.setStyleSheet(
            """
            QLabel {
                background: #191919;
                border: 1px solid #333333;
                padding: 15px;
                font-size: 14px;
            }

            QLabel a {
                color: #ffffff;
            }
            """
        )

        right_layout.addWidget(
            self.candidate_card,
            1
        )

        splitter.addWidget(
            right
        )

        splitter.setSizes(
            [450, 550, 600]
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        buttons = QHBoxLayout()

        self.keep_button = QPushButton(
            "✓ BEHOUD HUIDIGE"
        )

        self.keep_button.clicked.connect(
            self.keep_current
        )

        buttons.addWidget(
            self.keep_button
        )

        self.accept_button = QPushButton(
            "✓ KIES DEZE DISCOGS"
        )

        self.accept_button.setStyleSheet(
            """
            QPushButton {
                background: #294d2d;
                font-weight: bold;
                font-size: 16px;
            }

            QPushButton:hover {
                background: #356d3c;
            }
            """
        )

        self.accept_button.clicked.connect(
            self.accept_candidate
        )

        buttons.addWidget(
            self.accept_button
        )

        self.next_candidate_button = QPushButton(
            "✗ NIET DEZE"
        )

        self.next_candidate_button.clicked.connect(
            self.reject_candidate
        )

        buttons.addWidget(
            self.next_candidate_button
        )

        self.no_match_button = QPushButton(
            "Ø GEEN VAN DEZE"
        )

        self.no_match_button.clicked.connect(
            self.no_match
        )

        buttons.addWidget(
            self.no_match_button
        )

        self.next_release_button = QPushButton(
            "→ VOLGENDE VINYL"
        )

        self.next_release_button.clicked.connect(
            self.next_release
        )

        buttons.addWidget(
            self.next_release_button
        )

        self.stop_button = QPushButton(
            "STOP"
        )

        self.stop_button.clicked.connect(
            self.close
        )

        buttons.addWidget(
            self.stop_button
        )

        root.addLayout(
            buttons
        )

        # ====================================================
        # FOOTER
        # ====================================================

        self.status_label = QLabel(
            ""
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #aaaaaa;
                padding-top: 5px;
            }
            """
        )

        root.addWidget(
            self.status_label
        )


    # ========================================================
    # STATS
    # ========================================================

    def update_stats(self):

        total = len(
            self.releases
        )

        with_discogs = sum(
            1
            for row in self.releases
            if row["discogs"]
            and str(row["discogs"]).strip()
        )

        without_discogs = (
            total
            - with_discogs
        )

        live = (
            "LIVE OK"
            if self.session
            else "GEEN TOKEN"
        )

        self.stats_label.setText(
            f"COLLECTIE {total}"
            f"   |   "
            f"MET DISCOGS {with_discogs}"
            f"   |   "
            f"ZONDER DISCOGS {without_discogs}"
            f"   |   "
            f"GEREVIEWD {self.reviewed}"
            f"   |   "
            f"GEKOPPELD {self.matched}"
            f"   |   "
            f"{live}"
        )


    # ========================================================
    # SEARCH COLLECTION
    # ========================================================

    def search_collection(self):

        text = normalize(
            self.search_box.text()
        )

        mode = (
            self.filter_combo.currentIndex()
        )

        self.collection_table.setRowCount(
            0
        )

        displayed = 0

        for row in self.releases:

            has_discogs = bool(
                row["discogs"]
                and str(
                    row["discogs"]
                ).strip()
            )

            if mode == 1 and has_discogs:
                continue

            if mode == 2 and not has_discogs:
                continue

            if mode == 3:

                # In deze filter tonen we releases
                # die nog in onze huidige reviewlijst
                # zitten.
                #
                # Voor nu: alle resultaten.
                pass

            haystack = normalize(
                " ".join(
                    [
                        str(row["id"] or ""),
                        str(row["artist"] or ""),
                        str(row["title"] or ""),
                        str(row["label"] or ""),
                        str(row["catalog"] or ""),
                        str(row["storage_code"] or ""),
                        str(row["discogs"] or "")
                    ]
                )
            )

            if text and text not in haystack:
                continue

            self.collection_table.insertRow(
                displayed
            )

            values = [
                row["id"],
                row["artist"] or "",
                row["title"] or "",
                row["label"] or "",
                row["discogs"] or "-"
            ]

            for col, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                self.collection_table.setItem(
                    displayed,
                    col,
                    item
                )

            displayed += 1

            if displayed >= 800:
                break

        self.collection_table.resizeColumnsToContents()

    # ========================================================
    # LOAD RELEASE
    # ========================================================

    def load_release(self):

        self.update_stats()

        self.search_collection()

        if self.index >= len(
            self.releases
        ):

            self.finish()

            return

        release = self.releases[
            self.index
        ]

        self.current_release = release

        self.current_tracks = (
            self.tracks.get(
                release["id"],
                []
            )
        )

        self.display_release(
            release
        )

        self.display_tracks(
            self.current_tracks
        )

        # ----------------------------------------------------
        # CURRENT DISCogs
        # ----------------------------------------------------

        existing_id = (
            str(
                release["discogs"]
            )
            if release["discogs"]
            else ""
        )

        # ----------------------------------------------------
        # LOCAL
        # ----------------------------------------------------

        local_candidates = (
            self.local_candidates(
                release
            )
        )

        # ----------------------------------------------------
        # LIVE
        # ----------------------------------------------------

        live_candidates = []

        if (
            self.session
            and (
                not local_candidates
                or (
                    local_candidates
                    and local_candidates[0]["score"] < 70
                )
            )
        ):

            self.status_label.setText(
                "Discogs zoeken..."
            )

            QApplication.processEvents()

            try:

                live_candidates = live_search(
                    self.session,
                    release,
                    self.current_tracks
                )

            except Exception as exc:

                QMessageBox.warning(
                    self,
                    "Discogs",
                    str(exc)
                )

        # ----------------------------------------------------
        # COMBINE
        # ----------------------------------------------------

        candidates = []

        seen = set()

        # Current first
        if existing_id:

            for candidate in local_candidates:

                if (
                    str(
                        candidate["data"]["id"]
                    )
                    ==
                    existing_id
                ):

                    candidate["current"] = True

                    candidates.append(
                        candidate
                    )

                    seen.add(
                        existing_id
                    )

                    break

        # Others local
        for candidate in local_candidates:

            did = str(
                candidate["data"]["id"]
            )

            if did in seen:
                continue

            candidates.append(
                candidate
            )

            seen.add(did)

        # Live
        for item in live_candidates:

            candidate = live_candidate(
                item
            )

            did = str(
                candidate["id"]
            )

            if did in seen:
                continue

            score = score_candidate(
                release,
                candidate,
                self.current_tracks
            )

            candidates.append(
                {
                    "score": score,
                    "data": candidate,
                    "source": "LIVE",
                    "current": (
                        did == existing_id
                    )
                }
            )

            seen.add(did)

        candidates.sort(
            key=lambda x: (
                0
                if x.get("current")
                else 1,
                -x["score"]
            )
        )

        self.current_candidates = candidates[
            :MAX_CANDIDATES
        ]

        self.current_candidate_index = 0

        self.populate_candidate_table()

        if self.current_candidates:

            self.show_candidate()

        else:

            self.candidate_card.setText(
                """
                <h2>GEEN KANDIDATEN</h2>
                <p>
                Geen lokale of live Discogs-kandidaten
                gevonden.
                </p>
                """
            )

            self.disable_candidate_buttons()


    # ========================================================
    # LOCAL CANDIDATES
    # ========================================================

    def local_candidates(
        self,
        release
    ):

        candidates = []

        tracks = self.tracks.get(
            release["id"],
            []
        )

        for row in self.local_discogs:

            candidate = local_candidate(
                row
            )

            score = score_candidate(
                release,
                candidate,
                tracks
            )

            if score < 30:
                continue

            candidates.append(
                {
                    "score": score,
                    "data": candidate,
                    "source": "LOCAL",
                    "current": False
                }
            )

        candidates.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return candidates[:LOCAL_RESULTS]


    # ========================================================
    # DISPLAY RELEASE
    # ========================================================

    def display_release(
        self,
        release
    ):

        current = (
            release["discogs"]
            or "-"
        )

        status = (
            "HEEFT DISCOGS-ID"
            if release["discogs"]
            else "GEEN DISCOGS-ID"
        )

        artist = (
            release["artist"]
            or "-"
        )

        title = (
            release["title"]
            or "-"
        )

        html = f"""
        <h1>{artist}</h1>
        <h2>{title}</h2>

        <p>
        <b>Status:</b> {status}
        </p>

        <p>
        <b>Vault ID:</b>
        {release["id"]}
        </p>

        <p>
        <b>Label:</b>
        {release["label"] or "-"}
        </p>

        <p>
        <b>Catalog:</b>
        {release["catalog"] or "-"}
        </p>

        <p>
        <b>Year:</b>
        {release["year"] or "-"}
        </p>

        <p>
        <b>Storage:</b>
        {release["storage_code"] or "-"}
        </p>

        <p>
        <b>Genre:</b>
        {release["genre"] or "-"}
        </p>

        <hr>

        <p>
        <b>Huidige Discogs-ID:</b>
        {current}
        </p>
        """

        if release["discogs_link"]:

            html += (
                "<p>"
                "<b>Huidige Discogs-link:</b><br>"
                f"<a href=\"{release['discogs_link']}\">"
                f"{release['discogs_link']}"
                "</a>"
                "</p>"
            )

        self.release_card.setText(
            html
        )


    # ========================================================
    # DISPLAY TRACKS
    # ========================================================

    def display_tracks(
        self,
        tracks
    ):

        self.track_table.setRowCount(
            0
        )

        for index, track in enumerate(
            tracks
        ):

            self.track_table.insertRow(
                index
            )

            values = [
                track["position"] or "",
                track["artist"] or "",
                track["title"] or "",
                track["bpm"] or ""
            ]

            for column, value in enumerate(
                values
            ):

                self.track_table.setItem(
                    index,
                    column,
                    QTableWidgetItem(
                        str(value)
                    )
                )

        self.track_table.resizeColumnsToContents()


    # ========================================================
    # CANDIDATE TABLE
    # ========================================================

    def populate_candidate_table(
        self
    ):

        self.candidate_table.setRowCount(
            0
        )

        for index, candidate in enumerate(
            self.current_candidates
        ):

            self.candidate_table.insertRow(
                index
            )

            data = candidate["data"]

            values = [
                f"{candidate['score']:.1f}",
                (
                    "HUIDIG"
                    if candidate.get("current")
                    else candidate["source"]
                ),
                data["id"],
                data["artist"],
                data["title"],
                data["label"]
            ]

            for col, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value or "")
                )

                self.candidate_table.setItem(
                    index,
                    col,
                    item
                )

        self.candidate_table.resizeColumnsToContents()

        if self.current_candidates:

            self.candidate_table.selectRow(
                self.current_candidate_index
            )


    # ========================================================
    # SHOW CANDIDATE
    # ========================================================

    def show_candidate(self):

        if not self.current_candidates:

            return

        candidate = self.current_candidates[
            self.current_candidate_index
        ]

        data = candidate["data"]

        current = candidate.get(
            "current",
            False
        )

        existing_id = (
            self.current_release["discogs"]
            or ""
        )

        score = candidate["score"]

        second_score = 0

        for i, item in enumerate(
            self.current_candidates
        ):

            if i != self.current_candidate_index:

                if item["score"] > second_score:

                    second_score = item["score"]

        status = compare_status(
            score,
            score,
            second_score
        )

        html = f"""
        <h2>
        {data["artist"] or "-"}
        </h2>

        <h3>
        {data["title"] or "-"}
        </h3>

        <p>
        <b>Matchscore:</b>
        {score:.2f}
        </p>

        <p>
        <b>Status:</b>
        {status}
        </p>

        <p>
        <b>Bron:</b>
        {"HUIDIGE KOPPELING" if current else candidate["source"]}
        </p>

        <p>
        <b>Discogs ID:</b>
        {data["id"]}
        </p>

        <p>
        <b>Label:</b>
        {data["label"] or "-"}
        </p>

        <p>
        <b>Catalog:</b>
        {data["catalog"] or "-"}
        </p>

        <p>
        <b>Year:</b>
        {data["year"] or "-"}
        </p>

        <p>
        <b>Country:</b>
        {data["country"] or "-"}
        </p>

        <p>
        <b>Format:</b>
        {data["format"] or "-"}
        </p>
        """

        if data["kastcodes"]:

            html += (
                "<p><b>Kastcode:</b> "
                f"{data['kastcodes']}</p>"
            )

        if existing_id:

            if str(data["id"]) == str(existing_id):

                html += (
                    "<p><b>Dit is de huidige "
                    "koppeling.</b></p>"
                )

            else:

                html += (
                    "<p><b>Huidige ID:</b> "
                    f"{existing_id}</p>"
                )

        html += (
            "<hr>"
            "<p><b>Discogs:</b><br>"
            f"<a href=\"{data['url']}\">"
            f"{data['url']}"
            "</a></p>"
        )

        self.candidate_card.setText(
            html
        )

        self.candidate_table.selectRow(
            self.current_candidate_index
        )

        self.enable_candidate_buttons()

        self.status_label.setText(
            f"Kandidaat "
            f"{self.current_candidate_index + 1}/"
            f"{len(self.current_candidates)}"
        )


    # ========================================================
    # SELECT RELEASE
    # ========================================================

    def select_release_from_table(
        self,
        row,
        column
    ):

        item = (
            self.collection_table.item(
                row,
                0
            )
        )

        if item is None:
            return

        try:

            release_id = int(
                item.text()
            )

        except ValueError:

            return

        for index, release in enumerate(
            self.releases
        ):

            if release["id"] == release_id:

                self.index = index

                self.load_release()

                break


    # ========================================================
    # SELECT CANDIDATE
    # ========================================================

    def select_candidate(
        self,
        row,
        column
    ):

        if (
            row < 0
            or row >= len(
                self.current_candidates
            )
        ):

            return

        self.current_candidate_index = row

        self.show_candidate()


    # ========================================================
    # BUTTON STATES
    # ========================================================

    def disable_candidate_buttons(
        self
    ):

        self.keep_button.setEnabled(
            bool(
                self.current_release
                and self.current_release["discogs"]
            )
        )

        self.accept_button.setEnabled(
            False
        )

        self.next_candidate_button.setEnabled(
            False
        )

        self.no_match_button.setEnabled(
            True
        )


    def enable_candidate_buttons(
        self
    ):

        self.keep_button.setEnabled(
            bool(
                self.current_release["discogs"]
            )
        )

        self.accept_button.setEnabled(
            True
        )

        self.next_candidate_button.setEnabled(
            True
        )

        self.no_match_button.setEnabled(
            True
        )


    # ========================================================
    # BACKUP
    # ========================================================

    def create_backup(
        self
    ):

        if self.backup_created:
            return

        stamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup = os.path.join(
            os.path.dirname(DB),
            "vinylvault_BEFORE_FULL_REVIEW_"
            f"{stamp}.db"
        )

        shutil.copy2(
            DB,
            backup
        )

        self.backup_created = True

        QMessageBox.information(
            self,
            "Database backup",
            (
                "Er is een backup gemaakt voordat "
                "de eerste wijziging wordt opgeslagen.\n\n"
                f"{backup}"
            )
        )


    # ========================================================
    # ACCEPT CANDIDATE
    # ========================================================

    def accept_candidate(
        self
    ):

        if not self.current_candidates:
            return

        candidate = self.current_candidates[
            self.current_candidate_index
        ]

        data = candidate["data"]

        release = self.current_release

        if not data["id"]:
            return

        # Existing same ID = keep
        if (
            release["discogs"]
            and
            str(release["discogs"])
            ==
            str(data["id"])
        ):

            self.keep_current()

            return

        answer = QMessageBox.question(
            self,
            "Discogs koppelen",
            (
                "Deze Discogs-release als juiste "
                "versie instellen?\n\n"

                "VINYLVAULT\n"
                f"{release['artist'] or '-'} - "
                f"{release['title'] or '-'}\n"
                f"Label: {release['label'] or '-'}\n"
                f"Catalog: {release['catalog'] or '-'}\n\n"

                "DISCOGS\n"
                f"{data['artist'] or '-'} - "
                f"{data['title'] or '-'}\n"
                f"Label: {data['label'] or '-'}\n"
                f"Catalog: {data['catalog'] or '-'}\n\n"

                f"Discogs ID: {data['id']}\n"
                f"Score: {candidate['score']:.2f}"
            ),
            QMessageBox.StandardButton.Yes
            |
            QMessageBox.StandardButton.No
        )

        if (
            answer
            !=
            QMessageBox.StandardButton.Yes
        ):

            return

        try:

            self.create_backup()

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Backup fout",
                str(exc)
            )

            return

        link = (
            f"https://www.discogs.com/release/"
            f"{data['id']}"
        )

        try:

            self.conn.execute(
                """
                UPDATE releases
                SET
                    discogs = ?,
                    discogs_link = ?
                WHERE id = ?
                """,
                (
                    str(data["id"]),
                    link,
                    release["id"]
                )
            )

            self.conn.commit()

        except Exception as exc:

            self.conn.rollback()

            QMessageBox.critical(
                self,
                "Database fout",
                str(exc)
            )

            return

        self.matched += 1

        self.reviewed += 1

        self.index += 1

        self.load_release()


    # ========================================================
    # KEEP CURRENT
    # ========================================================

    def keep_current(
        self
    ):

        release = self.current_release

        if not release["discogs"]:

            return

        self.kept_current += 1

        self.reviewed += 1

        self.index += 1

        self.load_release()


    # ========================================================
    # REJECT CANDIDATE
    # ========================================================

    def reject_candidate(
        self
    ):

        if not self.current_candidates:
            return

        self.current_candidate_index += 1

        if (
            self.current_candidate_index
            >= len(
                self.current_candidates
            )
        ):

            self.candidate_card.setText(
                """
                <h2>GEEN KANDIDAAT MEER</h2>

                <p>
                Alle voorgestelde versies
                zijn afgewezen.
                </p>
                """
            )

            self.accept_button.setEnabled(
                False
            )

            self.next_candidate_button.setEnabled(
                False
            )

            return

        self.show_candidate()


    # ========================================================
    # NO MATCH
    # ========================================================

    def no_match(
        self
    ):

        self.reviewed += 1

        self.index += 1

        self.load_release()


    # ========================================================
    # NEXT RELEASE
    # ========================================================

    def next_release(
        self
    ):

        self.skipped += 1

        self.index += 1

        self.load_release()


    # ========================================================
    # FINISH
    # ========================================================

    def finish(
        self
    ):

        QMessageBox.information(
            self,
            "Review klaar",
            (
                "De volledige collectie-review is klaar.\n\n"
                f"Gekoppeld: {self.matched}\n"
                f"Huidige behouden: {self.kept_current}\n"
                f"Overgeslagen: {self.skipped}\n"
                f"Gereviewd: {self.reviewed}"
            )
        )

        self.close()


    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

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
    print(
        "KID ACID'S VINYLVAULT V3"
    )
    print(
        "FULL COLLECTION DISCOGS REVIEW"
    )
    print("=" * 80)

    print()
    print(
        "Database:"
    )

    print(
        DB
    )

    token = get_token()

    if token:

        print(
            "Discogs token: OK"
        )

    else:

        print(
            "Discogs token: NIET GEVONDEN"
        )

        print(
            "Lokale Discogs-data blijft beschikbaar."
        )

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Kid Acid's VinylVault V3"
    )

    window = FullReviewWindow()

    window.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()