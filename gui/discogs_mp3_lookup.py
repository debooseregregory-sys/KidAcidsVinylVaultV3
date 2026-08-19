from __future__ import annotations

import os
import re
from pathlib import Path

import requests

API_URL = "https://api.discogs.com"
USER_AGENT = "KidAcidsVinylVaultV3/1.0"


def _token() -> str:
    return os.environ.get("DISCOGS_TOKEN", "").strip()


def _headers() -> dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Discogs token={token}"
    return headers


def parse_filename(path: str) -> dict[str, str]:
    name = Path(path).stem.strip()
    result = {"track": "", "artist": "", "title": ""}

    # Common: 04 Artist - Title
    match = re.match(r"^\s*(\d{1,3})[\s._-]+(.+?)\s+-\s+(.+?)\s*$", name)
    if match:
        result["track"] = match.group(1).zfill(2)
        result["artist"] = match.group(2).strip()
        result["title"] = match.group(3).strip()
        return result

    # Common: A1 Artist - Title / B1 Artist - Title
    match = re.match(r"^\s*([A-Za-z]{1,2}\d{0,2})[\s._-]+(.+?)\s+-\s+(.+?)\s*$", name)
    if match:
        result["track"] = match.group(1).upper()
        result["artist"] = match.group(2).strip()
        result["title"] = match.group(3).strip()
        return result

    # No track number, but Artist - Title is still useful.
    match = re.match(r"^\s*(.+?)\s+-\s+(.+?)\s*$", name)
    if match:
        result["artist"] = match.group(1).strip()
        result["title"] = match.group(2).strip()
        return result

    return result


def search_releases(artist: str, title: str, limit: int = 10) -> list[dict]:
    artist = str(artist or "").strip()
    title = str(title or "").strip()
    if not artist and not title:
        return []

    params = {
        "type": "release",
        "q": " ".join(x for x in (artist, title) if x),
        "per_page": max(1, min(limit, 20)),
    }

    response = requests.get(
        f"{API_URL}/database/search",
        params=params,
        headers=_headers(),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])[:limit]


def get_release(release_id: str | int) -> dict:
    response = requests.get(
        f"{API_URL}/releases/{release_id}",
        headers=_headers(),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def artist_names(release: dict) -> str:
    names = []
    for artist in release.get("artists", []) or []:
        if isinstance(artist, dict) and artist.get("name"):
            names.append(str(artist["name"]).strip())
    return ", ".join(dict.fromkeys(names))


def label_info(release: dict) -> str:
    parts = []
    for item in release.get("labels", []) or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        catno = str(item.get("catno") or "").strip()
        if name and catno:
            parts.append(f"{name} [{catno}]")
        elif name:
            parts.append(name)
    return " | ".join(dict.fromkeys(parts))


def genre_text(release: dict) -> str:
    values = [str(x).strip() for x in (release.get("genres") or []) if str(x).strip()]
    values += [str(x).strip() for x in (release.get("styles") or []) if str(x).strip()]
    return ", ".join(dict.fromkeys(values))


def release_format(release: dict) -> str:
    values = []
    for item in release.get("formats", []) or []:
        if isinstance(item, dict) and item.get("name"):
            values.append(str(item["name"]).strip())
    return ", ".join(dict.fromkeys(values))


def composer_text(release: dict, track: dict | None = None) -> str:
    names = []

    def collect(items):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role") or "").strip().lower()
            name = str(item.get("name") or "").strip()
            if name and "composer" in role:
                names.append(name)

    collect((track or {}).get("extraartists") or [])
    collect(release.get("extraartists") or [])
    return ", ".join(dict.fromkeys(names))
