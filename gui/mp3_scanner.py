# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 FOLDER SCANNER
# Indexeert .mp3-bestanden van schijf naar mp3_files.
# ============================================================

from __future__ import annotations

from pathlib import Path

from database.database import get_connection

try:
    from mutagen.id3 import ID3, ID3NoHeaderError
    from mutagen.mp3 import MP3
    HAS_MUTAGEN = True
except Exception:
    HAS_MUTAGEN = False


def _text_frame(tags, key: str) -> str:
    if tags is None:
        return ""
    try:
        frame = tags.get(key)
        if frame is None:
            return ""
        text = frame.text[0] if getattr(frame, "text", None) else str(frame)
        return str(text).strip()
    except Exception:
        return ""


def read_tags(path: Path) -> dict:
    """Leest basis-ID3 tags; valt terug op bestandsnaam."""
    artist = ""
    title = ""
    album = ""
    year = None
    genre = ""
    bpm = None
    duration = 0
    bitrate = 0
    sample_rate = 0
    filesize = 0

    try:
        filesize = path.stat().st_size
    except OSError:
        pass

    stem = path.stem
    if " - " in stem:
        parts = stem.split(" - ", 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        title = stem

    if HAS_MUTAGEN:
        try:
            tags = ID3(str(path))
            artist = _text_frame(tags, "TPE1") or artist
            title = _text_frame(tags, "TIT2") or title
            album = _text_frame(tags, "TALB") or album
            genre = _text_frame(tags, "TCON") or genre
            year_text = _text_frame(tags, "TDRC") or _text_frame(tags, "TYER")
            if year_text:
                digits = "".join(ch for ch in year_text if ch.isdigit())
                if len(digits) >= 4:
                    try:
                        year = int(digits[:4])
                    except ValueError:
                        year = None
            bpm_text = _text_frame(tags, "TBPM")
            if bpm_text:
                try:
                    bpm = float(str(bpm_text).replace(",", "."))
                except ValueError:
                    bpm = None
        except ID3NoHeaderError:
            pass
        except Exception:
            pass

        try:
            audio = MP3(str(path))
            duration = int(audio.info.length) if audio.info and audio.info.length else 0
            bitrate = int(audio.info.bitrate) if audio.info and audio.info.bitrate else 0
            sample_rate = int(audio.info.sample_rate) if audio.info and audio.info.sample_rate else 0
        except Exception:
            pass

    return {
        "artist": artist,
        "title": title,
        "album": album,
        "year": year,
        "genre": genre,
        "bpm": bpm,
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "filesize": filesize,
        "filename": path.name,
        "path": str(path.resolve()),
    }


def scan_music_folder(
    folder: str | Path,
    progress_callback=None,
) -> dict:
    """
    Scant folder (recursief) op .mp3 en voegt nieuwe paden toe aan mp3_files.

    progress_callback(processed, total_found, added) — optioneel.

    Returns dict: found, added, skipped, errors, folder
    """
    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Map bestaat niet: {root}")

    # Bestaande paden (genormaliseerd) ophalen
    connection = get_connection()
    try:
        existing_rows = connection.execute(
            "SELECT path FROM mp3_files"
        ).fetchall()
    finally:
        connection.close()

    existing = set()
    for row in existing_rows:
        try:
            existing.add(str(Path(row[0]).resolve()))
        except Exception:
            existing.add(str(row[0]))

    # Alle mp3's op schijf
    paths = sorted(root.rglob("*.mp3"))
    # ook .MP3
    paths += sorted(p for p in root.rglob("*.MP3") if p not in paths)
    total = len(paths)

    added = 0
    skipped = 0
    errors = []

    connection = get_connection()
    try:
        for index, path in enumerate(paths, start=1):
            try:
                resolved = str(path.resolve())
            except Exception:
                resolved = str(path)

            if resolved in existing:
                skipped += 1
                if progress_callback:
                    progress_callback(index, total, added)
                continue

            try:
                meta = read_tags(path)
                connection.execute(
                    """
                    INSERT INTO mp3_files (
                        path, filename, artist, title, album,
                        duration, bitrate, sample_rate, bpm, genre, year, filesize
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meta["path"],
                        meta["filename"],
                        meta["artist"],
                        meta["title"],
                        meta["album"],
                        meta["duration"],
                        meta["bitrate"],
                        meta["sample_rate"],
                        meta["bpm"],
                        meta["genre"],
                        meta["year"],
                        meta["filesize"],
                    ),
                )
                existing.add(meta["path"])
                added += 1
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

            if progress_callback and (index % 25 == 0 or index == total):
                progress_callback(index, total, added)
                connection.commit()

        connection.commit()
    finally:
        connection.close()

    return {
        "folder": str(root),
        "found": total,
        "added": added,
        "skipped": skipped,
        "errors": errors,
    }
