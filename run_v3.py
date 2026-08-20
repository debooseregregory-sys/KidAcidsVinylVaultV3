from gui.mp3_showcase_playback_bridge import install_mp3_showcase_playback_bridge

# Install before the main window imports/creates the showcase page.
install_mp3_showcase_playback_bridge()

from gui.main_window import main

if __name__ == "__main__":
    main()
