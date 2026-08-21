# ============================================================
# KID ACID'S VINYLVAULT V3
# CD COLLECTION MODE
#
# CD collection uses the dedicated cd_releases table created by
# the CD module. Vinyl remains completely separate in releases.
# ============================================================

import sqlite3
from database.database import get_connection

VINYL = "VINYL"
CD = "CD"


def normalize_media_type(value):
    return CD if str(value or VINYL).strip().upper() == CD else VINYL


def ensure_media_type_column():
    """Compatibility helper for older databases."""
    conn = get_connection()
    try:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(releases)").fetchall()}
        if "media_type" not in columns:
            conn.execute("ALTER TABLE releases ADD COLUMN media_type TEXT DEFAULT 'VINYL'")
        conn.execute("UPDATE releases SET media_type='VINYL' WHERE media_type IS NULL OR TRIM(media_type)=''")
        conn.commit()
    finally:
        conn.close()


def _cd_table_exists(conn):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cd_releases'"
    ).fetchone() is not None


def _cd_columns(conn):
    return {row["name"] for row in conn.execute("PRAGMA table_info(cd_releases)").fetchall()}


class MediaReleaseLibraryPage:
    """Minimal CD library backed by cd_releases."""
    def __init__(self, parent=None, media_type=CD):
        from gui.release_library_page import ReleaseLibraryPage
        self._base = ReleaseLibraryPage(parent)
        self.media_type = normalize_media_type(media_type)
        self.release_selected = self._base.release_selected

    def __getattr__(self, name):
        return getattr(self._base, name)

    def load_releases(self):
        conn = get_connection()
        try:
            if not _cd_table_exists(conn):
                self._base.all_releases = []
                self._base.display_releases([])
                return
            cols = _cd_columns(conn)
            # The CD importer has used these core fields. Select only columns
            # that are guaranteed by the CD schema, with safe fallbacks.
            def c(name, fallback="NULL"):
                return f'cd."{name}"' if name in cols else fallback
            rows = conn.execute(f"""
                SELECT
                    {c('id','NULL')} AS id,
                    {c('artist',"''")} AS artist,
                    {c('title',"''")} AS title,
                    {c('label',"''")} AS label,
                    {c('catalog',"''")} AS catalog,
                    {c('year','NULL')} AS year,
                    {c('storage_code',"''")} AS storage_code,
                    {c('discogs',"''")} AS discogs,
                    {c('genre',"''")} AS genre,
                    {c('checked','0')} AS checked,
                    'CD' AS media_type,
                    0 AS tracks,
                    0 AS mp3_count
                FROM cd_releases cd
                ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
            """).fetchall()
        finally:
            conn.close()
        self._base.all_releases = rows
        self._base.display_releases(rows)

    def __getattribute__(self, name):
        if name in {"_base", "media_type", "release_selected", "load_releases", "__dict__", "__class__", "__getattr__", "__getattribute__"}:
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, "_base"), name)


class MediaReleaseBoardPage:
    """CD board backed by cd_releases."""
    def __init__(self, parent=None, media_type=CD):
        from gui.release_board_page import ReleaseBoardPage
        self._base = ReleaseBoardPage(parent)
        self.media_type = normalize_media_type(media_type)
        self.open_release = self._base.open_release
        self.play_mp3 = self._base.play_mp3

    def __getattribute__(self, name):
        if name in {"_base", "media_type", "open_release", "play_mp3", "load_releases", "__dict__", "__class__", "__getattribute__"}:
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, "_base"), name)

    def load_releases(self):
        conn = get_connection()
        try:
            if not _cd_table_exists(conn):
                self._base.all_releases = []
                self._base.apply_search()
                return
            cols = _cd_columns(conn)
            def c(name, fallback="NULL"):
                return f'cd."{name}"' if name in cols else fallback
            rows = conn.execute(f"""
                SELECT {c('id','NULL')} AS id,
                       {c('artist',"''")} AS artist,
                       {c('title',"''")} AS title,
                       {c('label',"''")} AS label,
                       {c('catalog',"''")} AS catalog,
                       {c('year','NULL')} AS year,
                       {c('storage_code',"''")} AS storage_code,
                       {c('checked','0')} AS checked,
                       {c('cover',"''")} AS cover,
                       NULL AS preferred_mp3
                FROM cd_releases cd
                ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
            """).fetchall()
            self._base.all_releases = [dict(row) for row in rows]
            self._base.apply_search()
        finally:
            conn.close()


class CDVinylVaultWindow:
    """CD-enabled window using the existing VinylVault UI."""
    def __new__(cls, *args, **kwargs):
        from gui.main_window import VinylVaultWindow
        obj = VinylVaultWindow(*args, **kwargs)
        cls._install(obj)
        return obj

    @staticmethod
    def _install(window):
        from PySide6.QtWidgets import QLabel
        from gui.cd_library_page import CDLibraryPage
        from gui.cd_board_page import CDBoardPage
        from gui.cd_discogs_import_page import CDDiscogsImportPage
        window.current_media_type = VINYL
        window.cd_library_page = CDLibraryPage()
        window.cd_board_page = CDBoardPage()
        window.cd_discogs_page = CDDiscogsImportPage()
        window.pages.addWidget(window.cd_library_page)
        window.pages.addWidget(window.cd_board_page)
        window.pages.addWidget(window.cd_discogs_page)
        window.cd_library_page.release_selected.connect(window._open_cd_release)
        window.cd_board_page.open_release.connect(window._show_cd_showcase)
        window.cd_board_page.play_mp3.connect(window.player_bar_play)
        window.cd_showcase_button.setEnabled(True)
        window.cd_library_button.setEnabled(True)
        window.cd_showcase_button.clicked.connect(window.show_cd_showcase_board)
        window.cd_library_button.clicked.connect(window.show_cd_library)
        footer = window.findChild(QLabel, "sidebarFooter")
        if footer:
            footer.setText("VINYL  •  CD  •  KID ACID")
        return window


def install_cd_mode():
    ensure_media_type_column()
    import gui.main_window as main_window_module
    # Prefer the dedicated CD window implementation already present in the
    # project. This module's table helpers are retained for compatibility.
    from gui.cd_mode import CDVinylVaultWindow as ExistingCDVinylVaultWindow
    main_window_module.VinylVaultWindow = ExistingCDVinylVaultWindow
