# ============================================================
# KID ACID'S VINYLVAULT V3
# APP SETTINGS (QSettings) + gedeelde helpers
# Compatibel met lokale discogs_import_page / cd_mode builds
# ============================================================

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor


ORG_NAME = "KidAcid"
APP_NAME = "VinylVaultV3"

# Keys
KEY_MUSIC_FOLDER = "music/folder"
KEY_DISCOGS_TOKEN = "discogs/token"
KEY_DISCOGS_USER_AGENT = "discogs/user_agent"
KEY_DISCOGS_CONSUMER_KEY = "discogs/consumer_key"
KEY_DISCOGS_CONSUMER_SECRET = "discogs/consumer_secret"
KEY_PREVIEW_BEFORE_IMPORT = "discogs/preview_before_import"
KEY_AUTO_MATCH_MP3 = "mp3/auto_match"
KEY_SCAN_ON_STARTUP = "mp3/scan_on_startup"


# ---------------------------------------------------------------------------
# Theme / paint
# ---------------------------------------------------------------------------

ACCENT = "#d84b91"
ACCENT_HOVER = "#f05ca4"
ACCENT_DARK = "#2b1a25"
BG_DARK = "#0b0b0f"
BG_PANEL = "#141419"
BG_INPUT = "#18181f"
BORDER = "#30303a"
TEXT = "#f2f2f5"
TEXT_MUTED = "#9b9ba6"


def paint_accent(alpha: int | float | None = None):
    """Accentkleur (#d84b91). Optioneel met alpha → QColor."""
    if alpha is None:
        return ACCENT
    color = QColor(ACCENT)
    if isinstance(alpha, float) and 0.0 <= alpha <= 1.0:
        color.setAlphaF(alpha)
    else:
        try:
            color.setAlpha(int(alpha))
        except Exception:
            color.setAlpha(255)
    return color


def paint_accent_hover() -> str:
    return ACCENT_HOVER


def paint_bg() -> str:
    return BG_DARK


def paint_panel() -> str:
    return BG_PANEL


def theme_colors() -> dict:
    return {
        "accent": ACCENT,
        "accent_hover": ACCENT_HOVER,
        "accent_dark": ACCENT_DARK,
        "bg": BG_DARK,
        "panel": BG_PANEL,
        "input": BG_INPUT,
        "border": BORDER,
        "text": TEXT,
        "muted": TEXT_MUTED,
    }


# ---------------------------------------------------------------------------
# QSettings helpers
# ---------------------------------------------------------------------------

def _settings() -> QSettings:
    return QSettings(ORG_NAME, APP_NAME)


def _get_str(key: str, default: str = "") -> str:
    value = _settings().value(key, default, type=str)
    return str(value or "").strip()


def _set_str(key: str, value: str) -> None:
    _settings().setValue(key, str(value or "").strip())
    _settings().sync()


def _get_bool(key: str, default: bool = False) -> bool:
    value = _settings().value(key, default)
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "on"):
        return True
    if text in ("0", "false", "no", "off", ""):
        return False
    return bool(value)


def _set_bool(key: str, value: bool) -> None:
    _settings().setValue(key, bool(value))
    _settings().sync()


# ---------------------------------------------------------------------------
# Music folder
# ---------------------------------------------------------------------------

def get_music_folder() -> str:
    return _get_str(KEY_MUSIC_FOLDER)


def set_music_folder(path: str) -> None:
    _set_str(KEY_MUSIC_FOLDER, path)


def get_music_folder_path() -> Path | None:
    folder = get_music_folder()
    if not folder:
        return None
    path = Path(folder).expanduser()
    return path if path.is_dir() else None


# ---------------------------------------------------------------------------
# Discogs credentials
# ---------------------------------------------------------------------------

def get_discogs_token() -> str:
    token = _get_str(KEY_DISCOGS_TOKEN)
    if token:
        return token
    try:
        import config
        token = (
            getattr(config, "DISCOGS_TOKEN", None)
            or getattr(config, "DISCOGS_PERSONAL_TOKEN", None)
            or getattr(config, "PERSONAL_TOKEN", None)
            or ""
        )
        return str(token or "").strip()
    except Exception:
        return ""


def set_discogs_token(token: str) -> None:
    _set_str(KEY_DISCOGS_TOKEN, token)


def get_discogs_user_agent() -> str:
    agent = _get_str(KEY_DISCOGS_USER_AGENT)
    if agent:
        return agent
    try:
        import config
        return str(
            getattr(config, "DISCOGS_USER_AGENT", None)
            or "KidAcidsVinylVaultV3/1.0"
        ).strip()
    except Exception:
        return "KidAcidsVinylVaultV3/1.0"


def set_discogs_user_agent(agent: str) -> None:
    _set_str(KEY_DISCOGS_USER_AGENT, agent)


def get_discogs_consumer_key() -> str:
    key = _get_str(KEY_DISCOGS_CONSUMER_KEY)
    if key:
        return key
    try:
        import config
        return str(getattr(config, "DISCOGS_CONSUMER_KEY", "") or "").strip()
    except Exception:
        return ""


def set_discogs_consumer_key(key: str) -> None:
    _set_str(KEY_DISCOGS_CONSUMER_KEY, key)


def get_discogs_consumer_secret() -> str:
    secret = _get_str(KEY_DISCOGS_CONSUMER_SECRET)
    if secret:
        return secret
    try:
        import config
        return str(getattr(config, "DISCOGS_CONSUMER_SECRET", "") or "").strip()
    except Exception:
        return ""


def set_discogs_consumer_secret(secret: str) -> None:
    _set_str(KEY_DISCOGS_CONSUMER_SECRET, secret)


def get_discogs_headers(extra: dict | None = None) -> dict:
    headers = {
        "User-Agent": get_discogs_user_agent(),
        "Accept": "application/vnd.discogs.v2.plaintext+json",
    }
    token = get_discogs_token()
    if token:
        headers["Authorization"] = f"Discogs token={token}"
    if extra:
        headers.update(extra)
    return headers


def discogs_headers(extra: dict | None = None) -> dict:
    return get_discogs_headers(extra)


# ---------------------------------------------------------------------------
# Discogs import options
# ---------------------------------------------------------------------------

def preview_before_import_enabled() -> bool:
    """Of er eerst een preview getoond wordt vóór Discogs-import."""
    return _get_bool(KEY_PREVIEW_BEFORE_IMPORT, True)


def set_preview_before_import_enabled(enabled: bool) -> None:
    _set_bool(KEY_PREVIEW_BEFORE_IMPORT, enabled)


def get_preview_before_import() -> bool:
    """Alias."""
    return preview_before_import_enabled()


def set_preview_before_import(enabled: bool) -> None:
    set_preview_before_import_enabled(enabled)


# ---------------------------------------------------------------------------
# MP3 options
# ---------------------------------------------------------------------------

def auto_match_mp3_enabled() -> bool:
    return _get_bool(KEY_AUTO_MATCH_MP3, False)


def set_auto_match_mp3_enabled(enabled: bool) -> None:
    _set_bool(KEY_AUTO_MATCH_MP3, enabled)


def scan_on_startup_enabled() -> bool:
    return _get_bool(KEY_SCAN_ON_STARTUP, False)


def set_scan_on_startup_enabled(enabled: bool) -> None:
    _set_bool(KEY_SCAN_ON_STARTUP, enabled)


# ---------------------------------------------------------------------------
# Aliassen
# ---------------------------------------------------------------------------

get_token = get_discogs_token
set_token = set_discogs_token
