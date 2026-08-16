# ================================================================
# KID ACID'S VINYL VAULT V3
# review_collection.py
#
# CENTRALE COLLECTIE REVIEWER
#
# ================================================================

import os
import re
import sys
import sqlite3
import webbrowser
from pathlib import Path

import requests

from PySide6.QtCore import (
    Qt,
    QObject,
    Signal,
    QThread,
    QUrl,
)

from PySide6.QtGui import QFont

from PySide6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput,
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QProgressBar,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
)

# ================================================================
# PATHS / CONFIG
# ================================================================

BASE_DIR = Path(__file__).resolve().parent

try:
    import config

    DB_PATH = BASE_DIR / getattr(
        config,
        "DB_PATH",
        "data/vinylvault.db",
    )

    DISCOGS_CONSUMER_KEY = getattr(
        config,
        "DISCOGS_CONSUMER_KEY",
        "",
    )

    DISCOGS_CONSUMER_SECRET = getattr(
        config,
        "DISCOGS_CONSUMER_SECRET",
        "",
    )

    DISCOGS_USER_AGENT = getattr(
        config,
        "DISCOGS_USER_AGENT",
        "KidAcidsVinylVaultV3/1.0",
    )

except Exception as exc:

    print("CONFIG FOUT:", exc)

    DB_PATH = (
        BASE_DIR
        / "data"
        / "vinylvault.db"
    )

    DISCOGS_CONSUMER_KEY = ""
    DISCOGS_CONSUMER_SECRET = ""

    DISCOGS_USER_AGENT = (
        "KidAcidsVinylVaultV3/1.0"
    )


# ================================================================
# MP3 ROOT
# ================================================================

DEFAULT_MP3_ROOT = Path(
    r"D:\01. MP3's"
)

if not DEFAULT_MP3_ROOT.exists():

    alternative = Path(
        r"D:\01. MP3’s"
    )

    if alternative.exists():
        DEFAULT_MP3_ROOT = alternative


# ================================================================
# DISCOGS
# ================================================================

DISCOGS_API = (
    "https://api.discogs.com"
)

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": DISCOGS_USER_AGENT,
        "Accept": "application/json",
    }
)

if DISCOGS_CONSUMER_KEY:

    SESSION.headers.update(
        {
            "Authorization": (
                f"Discogs key={DISCOGS_CONSUMER_KEY}, "
                f"secret={DISCOGS_CONSUMER_SECRET}"
            )
        }
    )


# ================================================================
# DATABASE
# ================================================================

def db_connect():

    conn = sqlite3.connect(
        str(DB_PATH),
        timeout=30,
    )

    conn.row_factory = sqlite3.Row

    return conn


def table_exists(
    conn,
    table,
):

    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?
        """,
        (table,),
    ).fetchone()

    return row is not None


def table_columns(
    conn,
    table,
):

    if not table_exists(
        conn,
        table,
    ):
        return set()

    rows = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


def ensure_review_columns():

    conn = db_connect()

    try:

        if not table_exists(
            conn,
            "releases",
        ):

            raise RuntimeError(
                "Tabel 'releases' bestaat niet."
            )

        release_cols = table_columns(
            conn,
            "releases",
        )

        additions = {

            "review_status":
                "TEXT DEFAULT 'OPEN'",

            "reviewed_at":
                "TEXT",

            "review_discogs_id":
                "TEXT",

            "review_discogs_link":
                "TEXT",

            "review_source":
                "TEXT",
        }

        for (
            name,
            definition,
        ) in additions.items():

            if name not in release_cols:

                conn.execute(
                    f"""
                    ALTER TABLE releases
                    ADD COLUMN {name} {definition}
                    """
                )

        # --------------------------------------------------------
        # TRACK MP3
        # --------------------------------------------------------

        if table_exists(
            conn,
            "tracks",
        ):

            track_cols = table_columns(
                conn,
                "tracks",
            )

            if "mp3_path" not in track_cols:

                conn.execute(
                    """
                    ALTER TABLE tracks
                    ADD COLUMN mp3_path TEXT
                    """
                )

        conn.commit()

    finally:

        conn.close()


# ================================================================
# COLLECTION
# ================================================================

def get_open_releases():

    conn = db_connect()

    try:

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
                storage_code,
                notes,
                review_status,
                review_discogs_id,
                review_discogs_link,
                review_source
            FROM releases
            WHERE COALESCE(
                review_status,
                'OPEN'
            ) != 'DONE'
            ORDER BY id
            """
        ).fetchall()

    finally:

        conn.close()


def get_tracks(
    release_id,
):

    conn = db_connect()

    try:

        cols = table_columns(
            conn,
            "tracks",
        )

        mp3_column = (
            "mp3_path"
            if "mp3_path" in cols
            else "NULL"
        )

        return conn.execute(
            f"""
            SELECT
                id,
                position,
                artist,
                title,
                duration,
                bpm,
                genre,
                notes,
                {mp3_column} AS mp3_path
            FROM tracks
            WHERE release_id = ?
            ORDER BY id
            """,
            (release_id,),
        ).fetchall()

    finally:

        conn.close()


# ================================================================
# RELEASE UPDATE
# ================================================================

def update_storage_code(
    release_id,
    storage_code,
):

    conn = db_connect()

    try:

        cols = table_columns(
            conn,
            "releases",
        )

        if "storage_code" not in cols:

            raise RuntimeError(
                "Kolom storage_code bestaat niet."
            )

        conn.execute(
            """
            UPDATE releases
            SET storage_code = ?
            WHERE id = ?
            """,
            (
                storage_code,
                release_id,
            ),
        )

        conn.commit()

    finally:

        conn.close()


# ================================================================
# TRACK UPDATE
# ================================================================

def update_track_position(
    track_id,
    position,
):

    conn = db_connect()

    try:

        conn.execute(
            """
            UPDATE tracks
            SET position = ?
            WHERE id = ?
            """,
            (
                position,
                track_id,
            ),
        )

        conn.commit()

    finally:

        conn.close()


def update_track_mp3(
    track_id,
    mp3_path,
):

    conn = db_connect()

    try:

        cols = table_columns(
            conn,
            "tracks",
        )

        if "mp3_path" not in cols:

            conn.execute(
                """
                ALTER TABLE tracks
                ADD COLUMN mp3_path TEXT
                """
            )

        conn.execute(
            """
            UPDATE tracks
            SET mp3_path = ?
            WHERE id = ?
            """,
            (
                mp3_path,
                track_id,
            ),
        )

        conn.commit()

    finally:

        conn.close()


# ================================================================
# SAVE REVIEW
# ================================================================

def save_review(
    release_id,
    discogs_id,
    discogs_link,
    source,
):

    conn = db_connect()

    try:

        cols = table_columns(
            conn,
            "releases",
        )

        updates = []
        values = []

        if "review_status" in cols:

            updates.append(
                "review_status = 'DONE'"
            )

        if "reviewed_at" in cols:

            updates.append(
                "reviewed_at = CURRENT_TIMESTAMP"
            )

        if "review_discogs_id" in cols:

            updates.append(
                "review_discogs_id = ?"
            )

            values.append(
                discogs_id
            )

        if "review_discogs_link" in cols:

            updates.append(
                "review_discogs_link = ?"
            )

            values.append(
                discogs_link
            )

        if "review_source" in cols:

            updates.append(
                "review_source = ?"
            )

            values.append(
                source
            )

        if "discogs" in cols:

            updates.append(
                "discogs = ?"
            )

            values.append(
                discogs_id or ""
            )

        if "discogs_link" in cols:

            updates.append(
                "discogs_link = ?"
            )

            values.append(
                discogs_link or ""
            )

        if not updates:

            raise RuntimeError(
                "Geen reviewvelden gevonden."
            )

        values.append(
            release_id
        )

        conn.execute(
            f"""
            UPDATE releases
            SET {", ".join(updates)}
            WHERE id = ?
            """,
            values,
        )

        conn.commit()

    finally:

        conn.close()


# ================================================================
# TEXT HELPERS
# ================================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


def norm(value):

    value = clean(value).lower()

    replacements = {

        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": "...",
        "Ã—": "x",

        "&": " and ",
        "_": " ",
        "/": " ",
        "-": " ",
    }

    for old, new in replacements.items():

        value = value.replace(
            old,
            new,
        )

    value = re.sub(
        r"[^\w\s]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def tokens(value):

    return {
        x
        for x in norm(value).split()
        if len(x) >= 2
    }


def token_score(
    a,
    b,
):

    ta = tokens(a)
    tb = tokens(b)

    if not ta or not tb:
        return 0.0

    intersection = len(
        ta & tb
    )

    union = len(
        ta | tb
    )

    if union == 0:
        return 0.0

    return (
        intersection
        / union
    ) * 100.0


def artist_score(
    local,
    remote,
):

    a = norm(local)
    b = norm(remote)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    if a in b or b in a:
        return 85.0

    return token_score(
        a,
        b,
    )


def title_score(
    local,
    remote,
):

    a = norm(local)
    b = norm(remote)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    if a in b or b in a:
        return 90.0

    return token_score(
        a,
        b,
    )


def label_matches(
    local_label,
    remote_labels,
):

    local = norm(
        local_label
    )

    if not local:
        return True

    remote_text = " ".join(
        norm(x)
        for x in remote_labels
        if clean(x)
    )

    if not remote_text:
        return False

    if local in remote_text:
        return True

    local_tokens = tokens(
        local
    )

    remote_tokens = tokens(
        remote_text
    )

    if (
        local_tokens
        and local_tokens <= remote_tokens
    ):
        return True

    return False


# ================================================================
# DISCOGS CANDIDATE
# ================================================================

class DiscogsCandidate:

    def __init__(
        self,
        release_id="",
        title="",
        artist="",
        label="",
        catalog="",
        year="",
        country="",
        format_text="",
        thumb="",
        uri="",
        score=0.0,
        label_ok=False,
    ):

        self.release_id = clean(
            release_id
        )

        self.title = clean(
            title
        )

        self.artist = clean(
            artist
        )

        self.label = clean(
            label
        )

        self.catalog = clean(
            catalog
        )

        self.year = clean(
            year
        )

        self.country = clean(
            country
        )

        self.format_text = clean(
            format_text
        )

        self.thumb = clean(
            thumb
        )

        self.uri = clean(
            uri
        )

        self.score = float(
            score or 0
        )

        self.label_ok = bool(
            label_ok
        )

    @property
    def link(self):

        if self.release_id:

            return (
                "https://www.discogs.com/release/"
                + self.release_id
            )

        return self.uri


# ================================================================
# DISCOGS SEARCH
# ================================================================

def discogs_search(
    artist,
    title,
    label,
    catalog,
    year,
):

    if not DISCOGS_CONSUMER_KEY:

        raise RuntimeError(
            "Discogs Consumer Key ontbreekt in config.py"
        )

    queries = []

    if catalog:

        queries.append(
            {
                "catno": catalog,
                "label": label,
            }
        )

    if artist or title:

        queries.append(
            {
                "artist": artist,
                "release_title": title,
            }
        )

    if title:

        queries.append(
            {
                "q": title,
            }
        )

    candidates = {}

    for params in queries:

        params = {
            k: v
            for k, v in params.items()
            if clean(v)
        }

        if not params:
            continue

        params["type"] = "release"
        params["per_page"] = 30

        try:

            response = SESSION.get(
                f"{DISCOGS_API}/database/search",
                params=params,
                timeout=20,
            )

            if response.status_code != 200:
                continue

            data = response.json()

        except Exception:

            continue

        for item in data.get(
            "results",
            [],
        ):

            rid = clean(
                item.get("id")
            )

            if not rid:
                continue

            candidates[rid] = item

    result = []

    for item in candidates.values():

        remote_title = clean(
            item.get("title")
        )

        remote_year = clean(
            item.get("year")
        )

        remote_labels = [
            clean(x)
            for x in item.get(
                "label",
                [],
            )
        ]

        remote_catalogs = [
            clean(x)
            for x in item.get(
                "catno",
                [],
            )
        ]

        remote_artist = remote_title
        remote_title_only = remote_title

        if " - " in remote_title:

            remote_artist = (
                remote_title.split(
                    " - ",
                    1,
                )[0]
            )

            remote_title_only = (
                remote_title.split(
                    " - ",
                    1,
                )[1]
            )

        a_score = artist_score(
            artist,
            remote_artist,
        )

        t_score = title_score(
            title,
            remote_title_only,
        )

        cat_score = 0.0

        if catalog and remote_catalogs:

            local_cat = norm(
                catalog
            )

            for remote_cat in remote_catalogs:

                remote_cat_norm = norm(
                    remote_cat
                )

                if (
                    local_cat
                    == remote_cat_norm
                ):

                    cat_score = 100.0
                    break

                if (
                    local_cat in remote_cat_norm
                    or remote_cat_norm in local_cat
                ):

                    cat_score = max(
                        cat_score,
                        75.0,
                    )

        label_ok = label_matches(
            label,
            remote_labels,
        )

        year_score = 0.0

        if year and remote_year:

            if clean(year) == remote_year:

                year_score = 10.0

        score = (
            a_score * 0.35
            + t_score * 0.35
            + cat_score * 0.25
            + year_score
        )

        if label and not label_ok:

            score -= 30.0

        candidate = DiscogsCandidate(
            release_id=item.get("id"),
            title=remote_title_only,
            artist=remote_artist,
            label=", ".join(
                remote_labels
            ),
            catalog=", ".join(
                remote_catalogs
            ),
            year=remote_year,
            country=clean(
                item.get("country")
            ),
            format_text=", ".join(
                item.get(
                    "format",
                    [],
                )
            ),
            thumb=clean(
                item.get("thumb")
            ),
            uri=clean(
                item.get("uri")
            ),
            score=score,
            label_ok=label_ok,
        )

        result.append(
            candidate
        )

    result.sort(
        key=lambda x: (
            x.label_ok,
            x.score,
        ),
        reverse=True,
    )

    if label:

        result = [
            x
            for x in result
            if x.label_ok
        ]

    return result[:20]


# ================================================================
# SEARCH WORKER
# ================================================================

class SearchWorker(QObject):

    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        artist,
        title,
        label,
        catalog,
        year,
    ):

        super().__init__()

        self.artist = artist
        self.title = title
        self.label = label
        self.catalog = catalog
        self.year = year

    def run(self):

        try:

            result = discogs_search(
                self.artist,
                self.title,
                self.label,
                self.catalog,
                self.year,
            )

            self.finished.emit(
                result
            )

        except Exception as exc:

            self.error.emit(
                str(exc)
            )


# ================================================================
# MP3 HELPERS
# ================================================================

def clean_filename(
    value,
):

    value = clean(
        value
    )

    value = re.sub(
        r"\.mp3$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\[[^\]]*\]",
        " ",
        value,
    )

    value = re.sub(
        r"\([^)]*\)",
        " ",
        value,
    )

    value = re.sub(
        r"[_\-]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return norm(
        value
    )


def filename_score(
    filename,
    artist,
    title,
):

    fn = clean_filename(
        filename
    )

    a = norm(
        artist
    )

    t = norm(
        title
    )

    if not fn:
        return 0

    score = 0

    if a and a in fn:
        score += 50

    if t and t in fn:
        score += 50

    combined = norm(
        f"{artist} {title}"
    )

    if combined and combined in fn:
        score += 30

    return score


def find_mp3_candidates(
    artist,
    title,
    root,
    limit=30,
):

    root = Path(
        root
    )

    if not root.exists():
        return []

    results = []

    artist_norm = norm(
        artist
    )

    title_norm = norm(
        title
    )

    try:

        paths = root.rglob(
            "*.mp3"
        )

    except Exception:

        return []

    for path in paths:

        try:

            filename = path.stem

            score = filename_score(
                filename,
                artist,
                title,
            )

            if score < 50:
                continue

            text_norm = clean_filename(
                filename
            )

            artist_match = (
                bool(artist_norm)
                and artist_norm in text_norm
            )

            title_match = (
                bool(title_norm)
                and title_norm in text_norm
            )

            if not (
                artist_match
                or title_match
            ):
                continue

            results.append(
                (
                    score,
                    path,
                )
            )

        except Exception:
            continue

    results.sort(
        key=lambda x: (
            -x[0],
            str(x[1]).lower(),
        )
    )

    return results[:limit]


# ================================================================
# MP3 DIALOG
# ================================================================

class MP3CandidateDialog(QDialog):

    def __init__(
        self,
        parent,
        artist,
        title,
        results,
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "MP3 kandidaat kiezen"
        )

        self.resize(
            900,
            550,
        )

        self.results = results
        self.selected_path = None

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            QLabel(
                f"<b>{artist} — {title}</b><br>"
                f"{len(results)} kandidaten gevonden."
            )
        )

        self.list = QListWidget()

        for score, path in results:

            item = QListWidgetItem(
                f"{score:3.0f}  |  {path.name}"
            )

            item.setToolTip(
                str(path)
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                str(path),
            )

            self.list.addItem(
                item
            )

        self.list.setCurrentRow(
            0
        )

        layout.addWidget(
            self.list,
            1,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.accept_selection
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            buttons
        )

    def accept_selection(self):

        item = self.list.currentItem()

        if not item:
            return

        self.selected_path = Path(
            item.data(
                Qt.ItemDataRole.UserRole
            )
        )

        self.accept()


# ================================================================
# MAIN WINDOW
# ================================================================

class ReviewCollectionWindow(
    QMainWindow
):

    def __init__(self):

        super().__init__()

        ensure_review_columns()

        self.setWindowTitle(
            "Kid Acid's Vinyl Vault V3 - Collection Reviewer"
        )

        self.resize(
            1650,
            950,
        )

        self.releases = []

        self.current_index = -1

        self.current_release = None

        self.current_tracks = []

        self.current_track = None

        self.search_thread = None
        self.search_worker = None

        self.candidates = []

        self.mp3_candidates = []

        self.loading_tracks = False

        # --------------------------------------------------------
        # MEDIA PLAYER
        # --------------------------------------------------------

        self.media_player = QMediaPlayer(
            self
        )

        self.audio_output = QAudioOutput(
            self
        )

        self.media_player.setAudioOutput(
            self.audio_output
        )

        self.audio_output.setVolume(
            1.0
        )

        self.build_ui()

        self.load_open_releases()


# ================================================================
# UI
# ================================================================

    def build_ui(self):

        root = QWidget()

        self.setCentralWidget(
            root
        )

        main_layout = QVBoxLayout(
            root
        )

        # ========================================================
        # TOP
        # ========================================================

        top = QHBoxLayout()

        self.status_label = QLabel(
            "OPENSTAAND"
        )

        self.status_label.setFont(
            QFont(
                "Segoe UI",
                16,
                QFont.Weight.Bold,
            )
        )

        top.addWidget(
            self.status_label
        )

        top.addStretch()

        self.progress_label = QLabel(
            "0 / 0"
        )

        top.addWidget(
            self.progress_label
        )

        self.reload_button = QPushButton(
            "↻ Herladen"
        )

        self.reload_button.clicked.connect(
            self.load_open_releases
        )

        top.addWidget(
            self.reload_button
        )

        main_layout.addLayout(
            top
        )

        # ========================================================
        # SPLITTER
        # ========================================================

        splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

        main_layout.addWidget(
            splitter,
            1,
        )

        # ========================================================
        # LEFT
        # ========================================================

        left = QWidget()

        left_layout = QVBoxLayout(
            left
        )

        left_layout.addWidget(
            QLabel(
                "<b>OPENSTAAND</b>"
            )
        )

        self.open_list = QListWidget()

        self.open_list.currentRowChanged.connect(
            self.open_release_selected
        )

        left_layout.addWidget(
            self.open_list,
            1,
        )

        splitter.addWidget(
            left
        )

        # ========================================================
        # RIGHT
        # ========================================================

        right = QWidget()

        right_layout = QVBoxLayout(
            right
        )

        # ========================================================
        # COLLECTION RELEASE
        # ========================================================

        local_group = QGroupBox(
            "COLLECTIE RELEASE"
        )

        local_form = QFormLayout(
            local_group
        )

        self.artist_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.label_edit = QLineEdit()
        self.catalog_edit = QLineEdit()
        self.year_edit = QLineEdit()

        self.kastcode_edit = QLineEdit()

        self.local_discogs_edit = QLineEdit()

        for widget in (
            self.artist_edit,
            self.title_edit,
            self.label_edit,
            self.catalog_edit,
            self.year_edit,
            self.local_discogs_edit,
        ):

            widget.setReadOnly(
                True
            )

        local_form.addRow(
            "Artist:",
            self.artist_edit,
        )

        local_form.addRow(
            "Titel:",
            self.title_edit,
        )

        local_form.addRow(
            "Label:",
            self.label_edit,
        )

        local_form.addRow(
            "Catalogus:",
            self.catalog_edit,
        )

        local_form.addRow(
            "Jaar:",
            self.year_edit,
        )

        kast_row = QHBoxLayout()

        kast_row.addWidget(
            self.kastcode_edit,
            1,
        )

        self.save_kast_button = QPushButton(
            "Opslaan"
        )

        self.save_kast_button.clicked.connect(
            self.save_kastcode
        )

        kast_row.addWidget(
            self.save_kast_button
        )

        kast_widget = QWidget()

        kast_widget.setLayout(
            kast_row
        )

        local_form.addRow(
            "Kastcode:",
            kast_widget,
        )

        # --------------------------------------------------------
        # DISCOGS LINK
        # --------------------------------------------------------

        discogs_row = QHBoxLayout()

        discogs_row.addWidget(
            self.local_discogs_edit,
            1,
        )

        self.open_local_discogs_button = QPushButton(
            "Open Discogs"
        )

        self.open_local_discogs_button.clicked.connect(
            self.open_local_discogs
        )

        discogs_row.addWidget(
            self.open_local_discogs_button
        )

        discogs_widget = QWidget()

        discogs_widget.setLayout(
            discogs_row
        )

        local_form.addRow(
            "Huidige Discogs:",
            discogs_widget,
        )

        right_layout.addWidget(
            local_group
        )

        # ========================================================
        # TRACKS
        # ========================================================

        tracks_group = QGroupBox(
            "TRACKS / MP3"
        )

        tracks_layout = QVBoxLayout(
            tracks_group
        )

        self.tracks_table = QTableWidget()

        self.tracks_table.setColumnCount(
            6
        )

        self.tracks_table.setHorizontalHeaderLabels(
            [
                "Positie",
                "Artist",
                "Titel",
                "Duur",
                "MP3",
                "Actie",
            ]
        )

        self.tracks_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.tracks_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.tracks_table.itemSelectionChanged.connect(
            self.track_selected
        )

        self.tracks_table.itemChanged.connect(
            self.track_item_changed
        )

        header = (
            self.tracks_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        tracks_layout.addWidget(
            self.tracks_table,
            1,
        )

        # --------------------------------------------------------
        # MP3 BUTTONS
        # --------------------------------------------------------

        mp3_buttons = QHBoxLayout()

        self.mp3_status = QLabel(
            "Geen MP3 geselecteerd"
        )

        mp3_buttons.addWidget(
            self.mp3_status,
            1,
        )

        self.mp3_search_button = QPushButton(
            "🔎 Zoek MP3"
        )

        self.mp3_search_button.clicked.connect(
            self.search_current_mp3
        )

        mp3_buttons.addWidget(
            self.mp3_search_button
        )

        self.mp3_add_button = QPushButton(
            "➕ MP3 koppelen"
        )

        self.mp3_add_button.clicked.connect(
            self.add_mp3
        )

        mp3_buttons.addWidget(
            self.mp3_add_button
        )

        self.mp3_remove_button = QPushButton(
            "✕ MP3 verwijderen"
        )

        self.mp3_remove_button.clicked.connect(
            self.remove_mp3
        )

        mp3_buttons.addWidget(
            self.mp3_remove_button
        )

        self.mp3_play_button = QPushButton(
            "▶ Afspelen"
        )

        self.mp3_play_button.clicked.connect(
            self.play_current_mp3
        )

        mp3_buttons.addWidget(
            self.mp3_play_button
        )

        self.mp3_pause_button = QPushButton(
            "Ⅱ Pauze"
        )

        self.mp3_pause_button.clicked.connect(
            self.pause_mp3
        )

        mp3_buttons.addWidget(
            self.mp3_pause_button
        )

        self.mp3_stop_button = QPushButton(
            "■ STOP"
        )

        self.mp3_stop_button.clicked.connect(
            self.stop_mp3
        )

        mp3_buttons.addWidget(
            self.mp3_stop_button
        )

        tracks_layout.addLayout(
            mp3_buttons
        )

        right_layout.addWidget(
            tracks_group,
            2,
        )

        # ========================================================
        # DISCOGS SEARCH
        # ========================================================

        search_group = QGroupBox(
            "AUTOMATISCHE DISCOGS-ZOEKER"
        )

        search_layout = QVBoxLayout(
            search_group
        )

        self.search_status = QLabel(
            "Nog niet gezocht."
        )

        search_layout.addWidget(
            self.search_status
        )

        self.search_button = QPushButton(
            "🔎 Opnieuw zoeken"
        )

        self.search_button.clicked.connect(
            self.start_search
        )

        search_layout.addWidget(
            self.search_button
        )

        self.candidate_list = QListWidget()

        self.candidate_list.currentRowChanged.connect(
            self.candidate_selected
        )

        search_layout.addWidget(
            self.candidate_list,
            1,
        )

        right_layout.addWidget(
            search_group,
            2,
        )

        # ========================================================
        # MANUAL DISCOGS
        # ========================================================

        manual_group = QGroupBox(
            "HANDMATIGE EXACTE DISCOGS-RELEASE"
        )

        manual_layout = QGridLayout(
            manual_group
        )

        manual_layout.addWidget(
            QLabel(
                "Release-ID / URL:"
            ),
            0,
            0,
        )

        self.manual_edit = QLineEdit()

        self.manual_edit.setPlaceholderText(
            "1234567 of volledige Discogs release URL"
        )

        manual_layout.addWidget(
            self.manual_edit,
            0,
            1,
        )

        self.manual_button = QPushButton(
            "Gebruik exacte link"
        )

        self.manual_button.clicked.connect(
            self.use_manual_link
        )

        manual_layout.addWidget(
            self.manual_button,
            0,
            2,
        )

        right_layout.addWidget(
            manual_group
        )

        # ========================================================
        # SELECTED DISCOGS
        # ========================================================

        selected_group = QGroupBox(
            "GESELECTEERDE DISCOGS RELEASE"
        )

        selected_form = QFormLayout(
            selected_group
        )

        self.selected_id = QLineEdit()
        self.selected_title = QLineEdit()
        self.selected_artist = QLineEdit()
        self.selected_label = QLineEdit()
        self.selected_catalog = QLineEdit()

        for widget in (
            self.selected_id,
            self.selected_title,
            self.selected_artist,
            self.selected_label,
            self.selected_catalog,
        ):

            widget.setReadOnly(
                True
            )

        selected_form.addRow(
            "Release ID:",
            self.selected_id,
        )

        selected_form.addRow(
            "Artist:",
            self.selected_artist,
        )

        selected_form.addRow(
            "Titel:",
            self.selected_title,
        )

        selected_form.addRow(
            "Label:",
            self.selected_label,
        )

        selected_form.addRow(
            "Catalogus:",
            self.selected_catalog,
        )

        selected_link_row = QHBoxLayout()

        self.selected_link = QLineEdit()

        self.selected_link.setReadOnly(
            True
        )

        selected_link_row.addWidget(
            self.selected_link,
            1,
        )

        self.open_selected_button = QPushButton(
            "🌐 Open"
        )

        self.open_selected_button.clicked.connect(
            self.open_selected_discogs
        )

        selected_link_row.addWidget(
            self.open_selected_button
        )

        selected_link_widget = QWidget()

        selected_link_widget.setLayout(
            selected_link_row
        )

        selected_form.addRow(
            "Discogs:",
            selected_link_widget,
        )

        right_layout.addWidget(
            selected_group
        )

        # ========================================================
        # BOTTOM
        # ========================================================

        buttons = QHBoxLayout()

        self.prev_button = QPushButton(
            "← Vorige"
        )

        self.prev_button.clicked.connect(
            self.previous_release
        )

        buttons.addWidget(
            self.prev_button
        )

        self.skip_button = QPushButton(
            "Overslaan"
        )

        self.skip_button.clicked.connect(
            self.skip_release
        )

        buttons.addWidget(
            self.skip_button
        )

        buttons.addStretch()

        self.save_button = QPushButton(
            "✓ Opslaan + Volgende"
        )

        self.save_button.setMinimumHeight(
            50
        )

        self.save_button.setFont(
            QFont(
                "Segoe UI",
                12,
                QFont.Weight.Bold,
            )
        )

        self.save_button.clicked.connect(
            self.save_and_next
        )

        buttons.addWidget(
            self.save_button
        )

        right_layout.addLayout(
            buttons
        )

        splitter.addWidget(
            right
        )

        splitter.setSizes(
            [
                350,
                1300,
            ]
        )


# ================================================================
# OPEN RELEASES
# ================================================================

    def load_open_releases(
        self,
        select_first=True,
    ):

        self.releases = list(
            get_open_releases()
        )

        self.open_list.blockSignals(
            True
        )

        self.open_list.clear()

        for row in self.releases:

            artist = clean(
                row["artist"]
            )

            title = clean(
                row["title"]
            )

            label = clean(
                row["label"]
            )

            catalog = clean(
                row["catalog"]
            )

            kast = clean(
                row["storage_code"]
            )

            text = (
                f"{artist} — {title}"
            )

            if label:
                text += f" | {label}"

            if catalog:
                text += f" | {catalog}"

            if kast:
                text += f" | {kast}"

            item = QListWidgetItem(
                text
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                row["id"],
            )

            self.open_list.addItem(
                item
            )

        self.open_list.blockSignals(
            False
        )

        self.progress_label.setText(
            f"0 / {len(self.releases)}"
        )

        self.clear_release_view()

        if not self.releases:

            self.status_label.setText(
                "✓ GEEN OPENSTAANDE RELEASES"
            )

            return

        self.status_label.setText(
            f"OPENSTAAND: {len(self.releases)}"
        )

        if select_first:

            self.open_list.setCurrentRow(
                0
            )


# ================================================================
# SELECT RELEASE
# ================================================================

    def open_release_selected(
        self,
        row_index,
    ):

        if row_index < 0:
            return

        if row_index >= len(
            self.releases
        ):
            return

        release = self.releases[
            row_index
        ]

        self.load_release(
            release
        )


    def load_release(
        self,
        release,
    ):

        self.stop_mp3()

        self.current_release = release

        try:

            self.current_index = (
                self.releases.index(
                    release
                )
            )

        except ValueError:

            self.current_index = -1

        self.progress_label.setText(
            f"{self.current_index + 1} / "
            f"{len(self.releases)}"
        )

        self.artist_edit.setText(
            clean(
                release["artist"]
            )
        )

        self.title_edit.setText(
            clean(
                release["title"]
            )
        )

        self.label_edit.setText(
            clean(
                release["label"]
            )
        )

        self.catalog_edit.setText(
            clean(
                release["catalog"]
            )
        )

        self.year_edit.setText(
            clean(
                release["year"]
            )
        )

        self.kastcode_edit.setText(
            clean(
                release["storage_code"]
            )
        )

        existing_discogs = clean(
            release["discogs_link"]
        )

        if not existing_discogs:

            discogs_id = clean(
                release["discogs"]
            )

            if discogs_id:

                existing_discogs = (
                    "https://www.discogs.com/release/"
                    + discogs_id
                )

        self.local_discogs_edit.setText(
            existing_discogs
        )

        self.load_tracks(
            release["id"]
        )

        self.candidate_list.clear()

        self.candidates = []

        self.clear_selected()

        self.manual_edit.clear()

        self.search_status.setText(
            "Discogs wordt gezocht..."
        )

        self.start_search()


# ================================================================
# TRACKS
# ================================================================

    def load_tracks(
        self,
        release_id,
    ):

        self.loading_tracks = True

        self.tracks_table.blockSignals(
            True
        )

        self.tracks_table.clearContents()

        tracks = list(
            get_tracks(
                release_id
            )
        )

        self.current_tracks = tracks

        self.tracks_table.setRowCount(
            len(tracks)
        )

        for row_index, track in enumerate(
            tracks
        ):

            position = clean(
                track["position"]
            )

            artist = clean(
                track["artist"]
            )

            title = clean(
                track["title"]
            )

            duration = track["duration"]

            duration_text = ""

            if duration:

                try:

                    total_seconds = int(
                        float(duration)
                    )

                    minutes = (
                        total_seconds // 60
                    )

                    seconds = (
                        total_seconds % 60
                    )

                    duration_text = (
                        f"{minutes}:{seconds:02d}"
                    )

                except Exception:

                    duration_text = clean(
                        duration
                    )

            mp3_path = clean(
                track["mp3_path"]
            )

            mp3_text = (
                Path(mp3_path).name
                if mp3_path
                else "—"
            )

            # ----------------------------------------------------
            # POSITIE
            # ----------------------------------------------------

            position_item = QTableWidgetItem(
                position
            )

            position_item.setData(
                Qt.ItemDataRole.UserRole,
                track["id"],
            )

            position_item.setFlags(
                position_item.flags()
                | Qt.ItemFlag.ItemIsEditable
            )

            self.tracks_table.setItem(
                row_index,
                0,
                position_item,
            )

            # ----------------------------------------------------
            # ARTIST
            # ----------------------------------------------------

            artist_item = QTableWidgetItem(
                artist
            )

            artist_item.setFlags(
                artist_item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            self.tracks_table.setItem(
                row_index,
                1,
                artist_item,
            )

            # ----------------------------------------------------
            # TITEL
            # ----------------------------------------------------

            title_item = QTableWidgetItem(
                title
            )

            title_item.setFlags(
                title_item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            self.tracks_table.setItem(
                row_index,
                2,
                title_item,
            )

            # ----------------------------------------------------
            # DUUR
            # ----------------------------------------------------

            duration_item = QTableWidgetItem(
                duration_text
            )

            duration_item.setFlags(
                duration_item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            self.tracks_table.setItem(
                row_index,
                3,
                duration_item,
            )

            # ----------------------------------------------------
            # MP3
            # ----------------------------------------------------

            mp3_item = QTableWidgetItem(
                mp3_text
            )

            mp3_item.setToolTip(
                mp3_path
            )

            mp3_item.setData(
                Qt.ItemDataRole.UserRole,
                mp3_path,
            )

            mp3_item.setFlags(
                mp3_item.flags()
                & ~Qt.ItemFlag.ItemIsEditable
            )

            self.tracks_table.setItem(
                row_index,
                4,
                mp3_item,
            )

            # ----------------------------------------------------
            # ACTIE
            # ----------------------------------------------------

            action_widget = QWidget()

            action_layout = QHBoxLayout(
                action_widget
            )

            action_layout.setContentsMargins(
                2,
                2,
                2,
                2,
            )

            select_button = QPushButton(
                "Selecteer"
            )

            select_button.clicked.connect(
                lambda checked=False,
                r=row_index:
                self.select_track_row(r)
            )

            action_layout.addWidget(
                select_button
            )

            self.tracks_table.setCellWidget(
                row_index,
                5,
                action_widget,
            )

        self.tracks_table.blockSignals(
            False
        )

        self.loading_tracks = False

        if tracks:

            self.tracks_table.selectRow(
                0
            )

        else:

            self.current_track = None

            self.mp3_status.setText(
                "Geen tracks"
            )


    def select_track_row(
        self,
        row,
    ):

        if (
            row < 0
            or row >= self.tracks_table.rowCount()
        ):
            return

        self.tracks_table.selectRow(
            row
        )


    def track_selected(
        self,
    ):

        rows = (
            self.tracks_table
            .selectionModel()
            .selectedRows()
        )

        if not rows:

            self.current_track = None

            self.mp3_status.setText(
                "Geen track geselecteerd"
            )

            return

        row = rows[0].row()

        if (
            row < 0
            or row >= len(
                self.current_tracks
            )
        ):
            return

        self.current_track = (
            self.current_tracks[row]
        )

        mp3_path = clean(
            self.current_track["mp3_path"]
        )

        if mp3_path:

            self.mp3_status.setText(
                f"MP3: {Path(mp3_path).name}"
            )

        else:

            self.mp3_status.setText(
                "Geen MP3 gekoppeld"
            )


    def track_item_changed(
        self,
        item,
    ):

        if self.loading_tracks:
            return

        if item.column() != 0:
            return

        track_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not track_id:
            return

        position = item.text().strip()

        try:

            update_track_position(
                track_id,
                position,
            )

            for i, track in enumerate(
                self.current_tracks
            ):

                if track["id"] == track_id:

                    old = dict(track)

                    old["position"] = position

                    self.current_tracks[i] = old

                    break

            self.mp3_status.setText(
                "✓ Trackpositie opgeslagen"
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Track opslaan mislukt",
                str(exc),
            )


# ================================================================
# KASTCODE
# ================================================================

    def save_kastcode(
        self,
    ):

        if not self.current_release:
            return

        release_id = (
            self.current_release["id"]
        )

        value = (
            self.kastcode_edit
            .text()
            .strip()
        )

        try:

            update_storage_code(
                release_id,
                value,
            )

            # Belangrijk:
            # huidige release blijft actief.
            #
            # Alleen de lijsttekst aanpassen.

            for row_index, release in enumerate(
                self.releases
            ):

                if release["id"] == release_id:

                    self.open_list.item(
                        row_index
                    ).setText(
                        self.make_release_list_text(
                            release,
                            override_kast=value,
                        )
                    )

                    break

            self.search_status.setText(
                "✓ Kastcode opgeslagen"
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Kastcode opslaan mislukt",
                str(exc),
            )


    def make_release_list_text(
        self,
        release,
        override_kast=None,
    ):

        artist = clean(
            release["artist"]
        )

        title = clean(
            release["title"]
        )

        label = clean(
            release["label"]
        )

        catalog = clean(
            release["catalog"]
        )

        if override_kast is None:

            kast = clean(
                release["storage_code"]
            )

        else:

            kast = clean(
                override_kast
            )

        text = (
            f"{artist} — {title}"
        )

        if label:
            text += f" | {label}"

        if catalog:
            text += f" | {catalog}"

        if kast:
            text += f" | {kast}"

        return text


# ================================================================
# DISCOGS SEARCH
# ================================================================

    def start_search(
        self,
    ):

        if not self.current_release:
            return

        if (
            self.search_thread
            and self.search_thread.isRunning()
        ):
            return

        self.candidate_list.clear()

        self.candidates = []

        self.search_status.setText(
            "🔎 Discogs zoeken op achtergrond..."
        )

        self.search_button.setEnabled(
            False
        )

        release = self.current_release

        self.search_thread = QThread(
            self
        )

        self.search_worker = SearchWorker(
            clean(
                release["artist"]
            ),
            clean(
                release["title"]
            ),
            clean(
                release["label"]
            ),
            clean(
                release["catalog"]
            ),
            clean(
                release["year"]
            ),
        )

        self.search_worker.moveToThread(
            self.search_thread
        )

        self.search_thread.started.connect(
            self.search_worker.run
        )

        self.search_worker.finished.connect(
            self.search_finished
        )

        self.search_worker.error.connect(
            self.search_error
        )

        self.search_worker.finished.connect(
            self.search_thread.quit
        )

        self.search_worker.error.connect(
            self.search_thread.quit
        )

        self.search_thread.finished.connect(
            self.search_thread_finished
        )

        self.search_thread.start()


    def search_thread_finished(
        self,
    ):

        if self.search_worker:

            self.search_worker.deleteLater()

        if self.search_thread:

            self.search_thread.deleteLater()

        self.search_worker = None

        self.search_thread = None


    def search_finished(
        self,
        candidates,
    ):

        self.search_button.setEnabled(
            True
        )

        self.candidates = candidates

        self.candidate_list.clear()

        if not candidates:

            self.search_status.setText(
                "Geen geschikte automatische kandidaten gevonden."
            )

            self.search_status.setToolTip(
                "Gebruik eventueel de exacte Discogs-link."
            )

            return

        self.search_status.setText(
            f"{len(candidates)} kandidaten gevonden."
        )

        for candidate in candidates:

            text = (
                f"{candidate.score:5.1f}"
                f" | "
                f"{candidate.artist}"
                f" — "
                f"{candidate.title}"
            )

            text += (
                f" | Label: "
                f"{candidate.label}"
            )

            if candidate.catalog:

                text += (
                    f" | Cat: "
                    f"{candidate.catalog}"
                )

            if candidate.year:

                text += (
                    f" | "
                    f"{candidate.year}"
                )

            item = QListWidgetItem(
                text
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                candidate.release_id,
            )

            self.candidate_list.addItem(
                item
            )

        self.candidate_list.setCurrentRow(
            0
        )


    def search_error(
        self,
        message,
    ):

        self.search_button.setEnabled(
            True
        )

        self.search_status.setText(
            f"Discogs fout: {message}"
        )


# ================================================================
# CANDIDATE
# ================================================================

    def candidate_selected(
        self,
        index,
    ):

        if index < 0:
            return

        if index >= len(
            self.candidates
        ):
            return

        candidate = self.candidates[
            index
        ]

        self.selected_id.setText(
            candidate.release_id
        )

        self.selected_artist.setText(
            candidate.artist
        )

        self.selected_title.setText(
            candidate.title
        )

        self.selected_label.setText(
            candidate.label
        )

        self.selected_catalog.setText(
            candidate.catalog
        )

        self.selected_link.setText(
            candidate.link
        )


    def clear_selected(
        self,
    ):

        self.selected_id.clear()

        self.selected_artist.clear()

        self.selected_title.clear()

        self.selected_label.clear()

        self.selected_catalog.clear()

        self.selected_link.clear()


# ================================================================
# MANUAL DISCOGS
# ================================================================

    def extract_discogs_id(
        self,
        value,
    ):

        value = clean(
            value
        )

        if not value:
            return ""

        if value.isdigit():
            return value

        patterns = [
            r"/release/(\d+)",
            r"discogs\.com/release/(\d+)",
            r"/release/(\d+)-",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                value,
                re.IGNORECASE,
            )

            if match:

                return match.group(
                    1
                )

        return ""


    def use_manual_link(
        self,
    ):

        value = (
            self.manual_edit
            .text()
            .strip()
        )

        discogs_id = (
            self.extract_discogs_id(
                value
            )
        )

        if not discogs_id:

            QMessageBox.warning(
                self,
                "Ongeldige Discogs-link",
                (
                    "Geef een Discogs release-ID "
                    "of volledige release-URL."
                ),
            )

            return

        link = (
            "https://www.discogs.com/release/"
            + discogs_id
        )

        self.selected_id.setText(
            discogs_id
        )

        self.selected_link.setText(
            link
        )

        self.selected_artist.setText(
            "HANDMATIG"
        )

        self.selected_title.setText(
            "Exacte Discogs release"
        )

        self.selected_label.clear()

        self.selected_catalog.clear()

        self.search_status.setText(
            f"✓ Exacte release gekozen: {discogs_id}"
        )


# ================================================================
# OPEN DISCOGS
# ================================================================

    def open_selected_discogs(
        self,
    ):

        link = (
            self.selected_link
            .text()
            .strip()
        )

        if link:

            webbrowser.open(
                link
            )


    def open_local_discogs(
        self,
    ):

        link = (
            self.local_discogs_edit
            .text()
            .strip()
        )

        if link:

            webbrowser.open(
                link
            )


# ================================================================
# MP3 SEARCH
# ================================================================

    def search_current_mp3(
        self,
    ):

        if not self.current_track:

            QMessageBox.information(
                self,
                "Geen track",
                "Selecteer eerst een track.",
            )

            return

        artist = clean(
            self.current_track["artist"]
        )

        title = clean(
            self.current_track["title"]
        )

        self.mp3_search_button.setEnabled(
            False
        )

        QApplication.setOverrideCursor(
            Qt.CursorShape.WaitCursor
        )

        try:

            results = find_mp3_candidates(
                artist,
                title,
                DEFAULT_MP3_ROOT,
                30,
            )

        finally:

            QApplication.restoreOverrideCursor()

            self.mp3_search_button.setEnabled(
                True
            )

        self.mp3_candidates = results

        if not results:

            QMessageBox.information(
                self,
                "Geen MP3 gevonden",
                (
                    f"Geen goede MP3 gevonden voor:\n\n"
                    f"{artist} — {title}"
                ),
            )

            return

        dialog = MP3CandidateDialog(
            self,
            artist,
            title,
            results,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:

            if dialog.selected_path:

                self.link_mp3_to_current_track(
                    dialog.selected_path
                )


# ================================================================
# MP3 MANUAL ADD
# ================================================================

    def add_mp3(
        self,
    ):

        if not self.current_track:

            QMessageBox.information(
                self,
                "Geen track",
                "Selecteer eerst een track.",
            )

            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecteer MP3",
            str(DEFAULT_MP3_ROOT),
            "MP3 bestanden (*.mp3)",
        )

        if not path:
            return

        self.link_mp3_to_current_track(
            Path(path)
        )


    def link_mp3_to_current_track(
        self,
        path,
    ):

        if not self.current_track:
            return

        path = Path(
            path
        )

        if not path.exists():

            QMessageBox.warning(
                self,
                "MP3 bestaat niet",
                str(path),
            )

            return

        track_id = self.current_track["id"]

        try:

            update_track_mp3(
                track_id,
                str(path),
            )

            release_id = (
                self.current_release["id"]
            )

            # Track opnieuw laden.
            self.load_tracks(
                release_id
            )

            # Dezelfde track terug selecteren.
            for row_index, track in enumerate(
                self.current_tracks
            ):

                if track["id"] == track_id:

                    self.tracks_table.selectRow(
                        row_index
                    )

                    break

            self.mp3_status.setText(
                f"✓ MP3 gekoppeld: {path.name}"
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "MP3 koppelen mislukt",
                str(exc),
            )


# ================================================================
# MP3 REMOVE
# ================================================================

    def remove_mp3(
        self,
    ):

        if not self.current_track:

            QMessageBox.information(
                self,
                "Geen track",
                "Selecteer eerst een track.",
            )

            return

        current_path = clean(
            self.current_track["mp3_path"]
        )

        if not current_path:

            QMessageBox.information(
                self,
                "Geen MP3",
                "Deze track heeft geen MP3.",
            )

            return

        answer = QMessageBox.question(
            self,
            "MP3 verwijderen",
            (
                "Wil je de MP3-koppeling verwijderen?\n\n"
                f"{Path(current_path).name}\n\n"
                "Het bestand zelf wordt NIET verwijderd."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.stop_mp3()

        track_id = (
            self.current_track["id"]
        )

        try:

            update_track_mp3(
                track_id,
                "",
            )

            self.load_tracks(
                self.current_release["id"]
            )

            for row_index, track in enumerate(
                self.current_tracks
            ):

                if track["id"] == track_id:

                    self.tracks_table.selectRow(
                        row_index
                    )

                    break

            self.mp3_status.setText(
                "✓ MP3-koppeling verwijderd"
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "MP3 verwijderen mislukt",
                str(exc),
            )


# ================================================================
# MP3 PLAYER
# ================================================================

    def play_current_mp3(
        self,
    ):

        if not self.current_track:

            QMessageBox.information(
                self,
                "Geen track",
                "Selecteer eerst een track.",
            )

            return

        mp3_path = clean(
            self.current_track["mp3_path"]
        )

        if not mp3_path:

            QMessageBox.information(
                self,
                "Geen MP3",
                (
                    "Aan deze track is nog "
                    "geen MP3 gekoppeld."
                ),
            )

            return

        self.play_mp3(
            mp3_path
        )


    def play_mp3(
        self,
        mp3_path,
    ):

        mp3_path = clean(
            mp3_path
        )

        if not mp3_path:
            return

        path = Path(
            mp3_path
        )

        if not path.exists():

            QMessageBox.warning(
                self,
                "MP3 niet gevonden",
                (
                    "Bestand bestaat niet:\n\n"
                    f"{mp3_path}"
                ),
            )

            return

        try:

            self.media_player.stop()

            self.media_player.setSource(
                QUrl()
            )

            url = QUrl.fromLocalFile(
                str(
                    path.resolve()
                )
            )

            self.media_player.setSource(
                url
            )

            self.media_player.play()

            self.mp3_status.setText(
                f"▶ {path.name}"
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "MP3 afspelen mislukt",
                str(exc),
            )


    def pause_mp3(
        self,
    ):

        try:

            self.media_player.pause()

            self.mp3_status.setText(
                "Ⅱ MP3 gepauzeerd"
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "MP3 pauzeren mislukt",
                str(exc),
            )


    def stop_mp3(
        self,
    ):

        try:

            self.media_player.stop()

            self.media_player.setSource(
                QUrl()
            )

            self.mp3_status.setText(
                "■ MP3 gestopt"
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "MP3 stoppen mislukt",
                str(exc),
            )


# ================================================================
# SAVE + NEXT
# ================================================================

    def save_and_next(
        self,
    ):

        if not self.current_release:
            return

        # --------------------------------------------------------
        # KASTCODE
        # --------------------------------------------------------

        try:

            update_storage_code(
                self.current_release["id"],
                self.kastcode_edit
                .text()
                .strip(),
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Kastcode opslaan mislukt",
                str(exc),
            )

            return

        # --------------------------------------------------------
        # DISCOGS
        # --------------------------------------------------------

        discogs_id = (
            self.selected_id
            .text()
            .strip()
        )

        discogs_link = (
            self.selected_link
            .text()
            .strip()
        )

        if not discogs_id:

            answer = QMessageBox.question(
                self,
                "Geen Discogs release",
                (
                    "Er is geen Discogs release geselecteerd.\n\n"
                    "Wil je deze release toch als gecontroleerd "
                    "opslaan en naar de volgende gaan?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if (
                answer
                != QMessageBox.StandardButton.Yes
            ):
                return

        if (
            not discogs_link
            and discogs_id
        ):

            discogs_link = (
                "https://www.discogs.com/release/"
                + discogs_id
            )

        source = "automatic"

        manual_value = (
            self.manual_edit
            .text()
            .strip()
        )

        if manual_value:

            manual_id = (
                self.extract_discogs_id(
                    manual_value
                )
            )

            if (
                manual_id
                and manual_id == discogs_id
            ):

                source = "manual"

        release_id = (
            self.current_release["id"]
        )

        try:

            save_review(
                release_id,
                discogs_id,
                discogs_link,
                source,
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Opslaan mislukt",
                str(exc),
            )

            return

        self.stop_mp3()

        # --------------------------------------------------------
        # UIT OPENSTAAND VERWIJDEREN
        # --------------------------------------------------------

        old_index = (
            self.current_index
        )

        if (
            0 <= old_index
            < len(self.releases)
        ):

            self.releases.pop(
                old_index
            )

            self.open_list.blockSignals(
                True
            )

            item = (
                self.open_list.takeItem(
                    old_index
                )
            )

            if item:
                del item

            self.open_list.blockSignals(
                False
            )

        self.current_release = None

        self.current_track = None

        self.clear_release_view()

        # --------------------------------------------------------
        # KLAAR
        # --------------------------------------------------------

        if not self.releases:

            self.status_label.setText(
                "✓ ALLES GECONTROLEERD"
            )

            self.progress_label.setText(
                "0 / 0"
            )

            return

        next_index = old_index

        if (
            next_index
            >= len(self.releases)
        ):

            next_index = (
                len(self.releases) - 1
            )

        self.open_list.setCurrentRow(
            next_index
        )

        self.status_label.setText(
            f"OPENSTAAND: {len(self.releases)}"
        )


# ================================================================
# SKIP
# ================================================================

    def skip_release(
        self,
    ):

        if not self.current_release:
            return

        if not self.releases:
            return

        next_index = (
            self.current_index + 1
        )

        if (
            next_index
            >= len(self.releases)
        ):

            next_index = 0

        self.open_list.setCurrentRow(
            next_index
        )


# ================================================================
# PREVIOUS
# ================================================================

    def previous_release(
        self,
    ):

        if not self.releases:
            return

        previous_index = (
            self.current_index - 1
        )

        if previous_index < 0:

            previous_index = (
                len(self.releases) - 1
            )

        self.open_list.setCurrentRow(
            previous_index
        )


# ================================================================
# CLEAR VIEW
# ================================================================

    def clear_release_view(
        self,
    ):

        self.artist_edit.clear()

        self.title_edit.clear()

        self.label_edit.clear()

        self.catalog_edit.clear()

        self.year_edit.clear()

        self.kastcode_edit.clear()

        self.local_discogs_edit.clear()

        self.tracks_table.clearContents()

        self.tracks_table.setRowCount(
            0
        )

        self.current_tracks = []

        self.current_track = None

        self.candidate_list.clear()

        self.search_status.setText(
            "Nog niet gezocht."
        )

        self.manual_edit.clear()

        self.clear_selected()

        self.mp3_status.setText(
            "Geen MP3 geselecteerd"
        )


# ================================================================
# WINDOW CLOSE
# ================================================================

    def closeEvent(
        self,
        event,
    ):

        try:

            self.media_player.stop()

            self.media_player.setSource(
                QUrl()
            )

        except Exception:
            pass

        if (
            self.search_thread
            and self.search_thread.isRunning()
        ):

            self.search_thread.quit()

            self.search_thread.wait(
                3000
            )

        event.accept()


# ================================================================
# MAIN
# ================================================================

def main():

    print(
        "=" * 70
    )

    print(
        "KID ACID'S VINYL VAULT V3"
    )

    print(
        "COLLECTION REVIEWER"
    )

    print(
        "=" * 70
    )

    print(
        f"Database: {DB_PATH}"
    )

    print(
        f"MP3 root: {DEFAULT_MP3_ROOT}"
    )

    print(
        "Discogs configuratie:"
    )

    print(
        "  Consumer Key:",
        (
            "gevonden"
            if DISCOGS_CONSUMER_KEY
            else "ONTBREEKT"
        ),
    )

    print(
        "  Consumer Secret:",
        (
            "gevonden"
            if DISCOGS_CONSUMER_SECRET
            else "ONTBREEKT"
        ),
    )

    print(
        "  User-Agent:",
        DISCOGS_USER_AGENT,
    )

    if not DB_PATH.exists():

        print(
            f"FOUT: database bestaat niet: {DB_PATH}"
        )

        return 1

    try:

        ensure_review_columns()

    except Exception as exc:

        print(
            "DATABASE FOUT:",
            exc,
        )

        return 1

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Kid Acid's Vinyl Vault V3"
    )

    window = (
        ReviewCollectionWindow()
    )

    window.show()

    return app.exec()


# ================================================================
# START
# ================================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )