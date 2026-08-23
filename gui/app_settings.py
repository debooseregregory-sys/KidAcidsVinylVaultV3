# ============================================================
# MusicVault shared settings helpers
# ============================================================

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox

ORG = "Kid Acid"
APP = "MusicVault"

ACCENT_COLORS = {
    "Rose": "#d84b91",
    "Crimson": "#c73b4f",
    "Electric": "#8f63ff",
    "Ice": "#55c9d8",
}

_PINK_HEXES = (
    "#d84b91", "#D84B91",
    "#ff4fa3", "#FF4FA3",
    "#e05299", "#E05299",
    "#ff67ad", "#FF67AD",
    "#ff6bb5", "#FF6BB5",
    "#ff6bb0", "#FF6BB0",
    "#e35ba0", "#E35BA0",
    "#ff8ec4", "#FF8EC4",
    "#e36aa5", "#E36AA5",
    "#f48fb1", "#F48FB1",
    "#ec407a", "#EC407A",
    "#e91e63", "#E91E63",
    "#ff5aa5", "#FF5AA5",
)


def settings_store():
    return QSettings(ORG, APP)


def get_bool(key, default=True):
    return settings_store().value(key, default, type=bool)


def get_str(key, default=""):
    return str(settings_store().value(key, default) or default)


def get_int(key, default=0):
    try:
        return int(settings_store().value(key, default))
    except (TypeError, ValueError):
        return int(default)


def accent_color():
    name = get_str("accent", "Rose")
    return ACCENT_COLORS.get(name, ACCENT_COLORS["Rose"])


def paint_accent(css: str) -> str:
    accent = accent_color()
    out = str(css or "")
    for pink in _PINK_HEXES:
        out = out.replace(pink, accent)
    return out


def density_name():
    name = get_str("density", "Comfortable")
    return name if name in ("Comfortable", "Compact") else "Comfortable"


def confirm_delete(parent, title, text):
    if not get_bool("confirm_before_deleting", True):
        return True
    answer = QMessageBox.question(
        parent,
        title,
        text,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return answer == QMessageBox.StandardButton.Yes


def notify(window, message, timeout_ms=3500):
    if not get_bool("show_notifications", True):
        return
    try:
        if window is not None and hasattr(window, "statusBar"):
            bar = window.statusBar()
            if bar is not None:
                bar.showMessage(str(message), int(timeout_ms))
                return
        w = window
        for _ in range(8):
            if w is None:
                break
            if hasattr(w, "statusBar"):
                try:
                    bar = w.statusBar()
                    if bar is not None:
                        bar.showMessage(str(message), int(timeout_ms))
                        return
                except Exception:
                    pass
            parent = getattr(w, "parent", None)
            w = parent() if callable(parent) else parent
    except Exception:
        pass
    print("NOTIFY:", message)


def cover_size(default_large=216, default_small=160):
    if get_bool("large_covers", True):
        return int(default_large)
    return int(default_small)


def artwork_animations_enabled():
    return get_bool("artwork_animations", True)


def import_artwork_enabled():
    return get_bool("import_artwork", True)


def enrich_metadata_enabled():
    return get_bool("enrich_metadata", True)


def preview_before_import_enabled():
    return get_bool("preview_before_import", True)


def never_overwrite_manual_enabled():
    return get_bool("never_overwrite_manual", True)


def backup_before_import_enabled():
    return get_bool("backup_before_import", True)


def discogs_match_mode():
    mode = get_str("discogs_match_mode", "Balanced")
    return mode if mode in ("Strict", "Balanced", "Flexible") else "Balanced"


def match_minimum_score(default_balanced=60):
    mode = discogs_match_mode()
    if mode == "Strict":
        return 80
    if mode == "Flexible":
        return 40
    return int(default_balanced)


def match_mp3_minimum_score():
    mode = discogs_match_mode()
    if mode == "Strict":
        return 750
    if mode == "Flexible":
        return 250
    return 450


def match_result_limit(default=10):
    mode = discogs_match_mode()
    if mode == "Strict":
        return max(3, min(default, 5))
    if mode == "Flexible":
        return max(default, 20)
    return default


def get_discogs_token():
    store = settings_store()
    for key in ("discogs_token", "DISCOGS_TOKEN", "token"):
        val = str(store.value(key, "") or "").strip()
        if val:
            return val
    return os.environ.get("DISCOGS_TOKEN", "").strip()


def get_discogs_headers():
    headers = {
        "User-Agent": (
            "KidAcidsVinylVaultV3/1.0 "
            "+https://github.com/debooseregregory-sys/KidAcidsVinylVaultV3"
        ),
        "Accept": "application/json",
    }
    token = get_discogs_token()
    if token:
        headers["Authorization"] = f"Discogs token={token}"
    return headers


def set_discogs_token(token: str):
    token = str(token or "").strip()
    store = settings_store()
    if token:
        store.setValue("discogs_token", token)
    else:
        store.remove("discogs_token")


def create_db_backup_copy():
    try:
        from database.database import DB_PATH
        src = Path(DB_PATH)
    except Exception:
        candidates = [
            Path("data/musicvault.db"),
            Path("database/musicvault.db"),
            Path("vinylvault.db"),
        ]
        src = next((p for p in candidates if p.exists()), None)
        if src is None:
            return None
    if not src.exists():
        return None
    from datetime import datetime
    import shutil
    backup_dir = src.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"{src.stem}_pre_import_{stamp}{src.suffix}"
    shutil.copy2(src, dest)
    return str(dest)
