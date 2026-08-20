from pathlib import Path


def install_mp3_showcase_playback_bridge():
    """Route MP3 Showcase playback directly to the application's working MP3Player."""
    from gui.mp3_showcase_page import MP3ShowcasePage

    if getattr(MP3ShowcasePage, "_playback_bridge_installed", False):
        return

    def play_path(self, path):
        path = str(path or "")
        if not path or not Path(path).exists():
            try:
                self.status.setText("MP3-bestand niet gevonden")
            except Exception:
                pass
            return False

        # The MP3 Library already uses the central player. Use that same object here.
        window = self.window()
        player = getattr(window, "mp3_player", None)
        if player is not None and hasattr(player, "play_file"):
            try:
                player.play_file(path)
                self.vinyl_deck.set_playing(True)
                return True
            except Exception as exc:
                try:
                    self.status.setText(f"Afspelen mislukt: {exc}")
                except Exception:
                    pass
                return False

        # Keep the existing signal as a fallback for alternate hosts.
        self.play_mp3.emit(path)
        self.vinyl_deck.set_playing(True)
        return True

    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            play_path(self, path)

    def play_track_item(self, item):
        path = str(item.data(256) or "")
        if path:
            play_path(self, path)

    def stop_current(self):
        self.vinyl_deck.set_playing(False)
        player = getattr(self.window(), "mp3_player", None)
        if player is not None and hasattr(player, "stop"):
            try:
                player.stop()
            except Exception:
                pass

    MP3ShowcasePage.play_current = play_current
    MP3ShowcasePage.play_track_item = play_track_item
    MP3ShowcasePage.stop_current = stop_current
    MP3ShowcasePage._playback_bridge_installed = True
