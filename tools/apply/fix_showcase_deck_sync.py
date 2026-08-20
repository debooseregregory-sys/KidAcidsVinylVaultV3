from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "gui" / "main_window.py"
SHOWCASE = ROOT / "gui" / "mp3_showcase_page.py"


def git_head(path):
    rel = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(
        ["git", "show", f"HEAD:{rel}"],
        cwd=ROOT,
    ).decode("utf-8-sig")


def restore_clean_sources():
    for path in (MAIN, SHOWCASE):
        path.write_text(git_head(path), encoding="utf-8", newline="\n")


def patch_showcase():
    s = SHOWCASE.read_text(encoding="utf-8-sig")

    if "def sync_external_play(" in s:
        return

    marker = "    def play_current(self):"
    if marker not in s:
        raise RuntimeError("play_current() niet gevonden in mp3_showcase_page.py")

    method = '''    def sync_external_play(self, path):\n        \"\"\"Synchroniseer de visuele vinyl-deck met centrale MP3 playback.\"\"\"\n        path = str(path or \"\").strip()\n        if not path:\n            return\n\n        artist = \"Onbekende artiest\"\n        title = Path(path).stem or \"-\"\n\n        try:\n            conn = get_connection()\n            try:\n                row = conn.execute(\n                    \"\"\"\n                    SELECT m.artist, m.title, r.artist, r.title\n                    FROM mp3_files m\n                    LEFT JOIN track_mp3 tm ON tm.mp3_id = m.id\n                    LEFT JOIN tracks t ON t.id = tm.track_id\n                    LEFT JOIN releases r ON r.id = t.release_id\n                    WHERE m.path = ?\n                    ORDER BY tm.id\n                    LIMIT 1\n                    \"\"\",\n                    (path,),\n                ).fetchone()\n            finally:\n                conn.close()\n\n            if row:\n                mp3_artist, mp3_title, release_artist, release_title = row\n                artist = str(mp3_artist or release_artist or artist).strip() or artist\n                title = str(mp3_title or release_title or title).strip() or title\n        except Exception as exc:\n            print(\"SHOWCASE DECK SYNC DB ERROR:\", exc)\n\n        self.vinyl_deck.set_track(artist, title)\n        self.vinyl_deck.set_playing(True)\n        self.status.setText(f\"PLAYING: {Path(path).name}\")\n\n'''
    s = s.replace(marker, method + marker, 1)
    SHOWCASE.write_text(s, encoding="utf-8", newline="\n")


def patch_main_window():
    s = MAIN.read_text(encoding="utf-8-sig")

    marker = '''        self.player_bar.play_file(\n            path\n        )'''
    if marker not in s:
        marker = '''        self.player_bar.play_file(path)'''
    if marker not in s:
        raise RuntimeError("player_bar.play_file() niet gevonden")

    if "sync_external_play" not in s:
        replacement = '''        # Houd de visuele vinyl-deck gelijk met elke centrale MP3-playback.\n        # Dit geldt dus ook wanneer een MP3 vanuit een andere pagina wordt gestart.\n        if hasattr(self, "mp3_showcase_page"):\n            self.mp3_showcase_page.sync_external_play(path)\n\n''' + marker
        s = s.replace(marker, replacement, 1)

    MAIN.write_text(s, encoding="utf-8", newline="\n")


def compile_check():
    subprocess.check_call(["python", "-m", "py_compile", str(MAIN), str(SHOWCASE)], cwd=ROOT)


if __name__ == "__main__":
    restore_clean_sources()
    patch_showcase()
    patch_main_window()
    compile_check()
    print("OK - centrale MP3 playback is nu gekoppeld aan de VinylDeck")
    print("OK - main_window.py en mp3_showcase_page.py zijn schoon hersteld vanaf HEAD")
