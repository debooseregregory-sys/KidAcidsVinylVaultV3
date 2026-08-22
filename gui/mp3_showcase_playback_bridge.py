from pathlib import Path
from types import MethodType

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


def _install_livesets(window, sidebar_layout=None):
    """Install the standalone Livesets Showcase/Library/detail pages into the main window.

    The current main window already calls this bridge during UI construction, so using
    that existing hook keeps the Livesets module isolated without disturbing the Vinyl,
    MP3 or CD pages.
    """
    if window is None or getattr(window, "_livesets_installed", False):
        return

    from gui.livesets_detail_page import LivesetDetailPage
    from gui.livesets_edit_page import LivesetsEditPage
    from gui.livesets_showcase_page import LivesetsShowcasePage

    if sidebar_layout is None:
        sidebar = window.findChild(type(window), "sidebar")
        if sidebar is not None:
            sidebar_layout = sidebar.layout()

    if sidebar_layout is None:
        return

    # --------------------------------------------------------
    # Pages
    # --------------------------------------------------------
    showcase = LivesetsShowcasePage()
    library = LivesetsEditPage()
    detail = LivesetDetailPage()

    window.pages.addWidget(showcase)
    window.pages.addWidget(library)
    window.pages.addWidget(detail)

    window.livesets_showcase_page = showcase
    window.livesets_library_page = library
    window.liveset_detail_page = detail

    # --------------------------------------------------------
    # Sidebar navigation: insert LIVESETS before the footer.
    # --------------------------------------------------------
    livesets_label = QLabel("LIVESETS")
    livesets_label.setObjectName("collectionSectionLabel")

    showcase_button = window.create_nav_button("◉", "Showcase")
    library_button = window.create_nav_button("▤", "Library")

    window.livesets_showcase_button = showcase_button
    window.livesets_library_button = library_button

    footer_index = sidebar_layout.count()
    for index in range(sidebar_layout.count()):
        item = sidebar_layout.itemAt(index)
        widget = item.widget()
        if widget is not None and widget.objectName() == "sidebarFooter":
            footer_index = index
            break

    sidebar_layout.insertWidget(footer_index, livesets_label)
    sidebar_layout.insertSpacing(footer_index + 1, 14)
    sidebar_layout.insertWidget(footer_index + 2, showcase_button)
    sidebar_layout.insertWidget(footer_index + 3, library_button)

    # --------------------------------------------------------
    # Navigation helpers.
    # --------------------------------------------------------
    original_set_active_nav = window.set_active_nav
    original_show_home = window.show_home
    original_show_library = window.show_library
    original_show_vinyl_showcase = window.show_vinyl_showcase
    original_show_mp3_showcase = window.show_mp3_showcase
    original_show_mp3_library = window.show_mp3_library
    original_show_discogs = window.show_discogs
    original_show_cd_library = window.show_cd_library

    def set_active_nav(self, button):
        original_set_active_nav(button)
        for item in (showcase_button, library_button):
            item.setProperty("active", item is button)
            item.style().unpolish(item)
            item.style().polish(item)
            item.update()

    window.set_active_nav = MethodType(set_active_nav, window)

    def show_livesets_showcase(self):
        showcase.reload()
        self.pages.setCurrentWidget(showcase)
        self.page_title.setText("Livesets Showcase")
        self.set_active_nav(showcase_button)

    def show_livesets_library(self):
        library.reload()
        self.pages.setCurrentWidget(library)
        self.page_title.setText("Livesets Library")
        self.set_active_nav(library_button)

    def show_liveset_detail(self, data):
        detail.load_liveset(data)
        self.pages.setCurrentWidget(detail)
        self.page_title.setText("Liveset")
        self.set_active_nav(showcase_button)

    window.show_livesets_showcase = MethodType(show_livesets_showcase, window)
    window.show_livesets_library = MethodType(show_livesets_library, window)
    window.show_liveset_detail = MethodType(show_liveset_detail, window)

    showcase_button.clicked.connect(window.show_livesets_showcase)
    library_button.clicked.connect(window.show_livesets_library)
    showcase.open_requested.connect(window.show_liveset_detail)
    detail.back_requested.connect(window.show_livesets_showcase)

    # --------------------------------------------------------
    # Live library changes immediately refresh the Showcase.
    # --------------------------------------------------------
    library.changed.connect(showcase.reload)

    # --------------------------------------------------------
    # Liveset playback always uses the central player.
    # --------------------------------------------------------
    showcase_open_playback = getattr(showcase, "play_mp3", None)
    if showcase_open_playback is not None:
        showcase_open_playback.connect(window.player_bar_play)

    detail.play_mp3.connect(window.player_bar_play)

    window._livesets_installed = True

    # Keep references to the original methods so this bootstrap remains transparent.
    window._livesets_original_nav_methods = {
        "show_home": original_show_home,
        "show_library": original_show_library,
        "show_vinyl_showcase": original_show_vinyl_showcase,
        "show_mp3_showcase": original_show_mp3_showcase,
        "show_mp3_library": original_show_mp3_library,
        "show_discogs": original_show_discogs,
        "show_cd_library": original_show_cd_library,
    }


def install_mp3_showcase_playback_bridge():
    """Route MP3 Showcase playback and install the standalone Livesets UI."""
    from gui.mp3_showcase_page import MP3ShowcasePage

    if not getattr(MP3ShowcasePage, "_playback_bridge_installed", False):
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

    # The bridge is invoked from VinylVaultWindow.build_ui after all page objects,
    # the central player and the sidebar have been constructed. The caller frame gives
    # us the actual main-window instance and its sidebar layout without changing the
    # existing main_window.py call site.
    try:
        import inspect

        frame = inspect.currentframe()
        caller = frame.f_back if frame is not None else None
        window = caller.f_locals.get("self") if caller is not None else None
        sidebar_layout = caller.f_locals.get("sidebar_layout") if caller is not None else None
        _install_livesets(window, sidebar_layout)
    except Exception:
        # The MP3 bridge must never prevent the application from starting.
        pass
