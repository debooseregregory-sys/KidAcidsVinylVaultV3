import sys
import time

from PySide6.QtWidgets import QApplication

from gui.cd_mode import install_cd_mode
from gui.startup_splash import StartupSplash


install_cd_mode()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kid Acid's MusicVault")
    app.setApplicationDisplayName("Kid Acid's MusicVault")
    app.setStyle("Fusion")

    splash = StartupSplash(duration=None)
    splash.show()
    app.processEvents()

    # The splash must be visible first. Build the main window while it stays
    # hidden, then keep the splash visible for at least five seconds.
    splash_started = time.monotonic()

    import gui.main_window as main_window
    from PySide6.QtCore import QSettings

    window = main_window.VinylVaultWindow()

    settings = QSettings("Kid Acid", "MusicVault")
    has_geometry = (
        settings.value("window_geometry") is not None
        and settings.value("remember_window_state", True, type=bool)
    )

    # Do NOT show the main window yet. It must only appear when the splash
    # disappears.
    if not has_geometry:
        window.showMaximized()
        window.hide()
    else:
        window.show()
        window.hide()

    app.processEvents()

    # Minimum splash duration: 5 seconds.
    remaining = 5.0 - (time.monotonic() - splash_started)
    if remaining > 0:
        time.sleep(remaining)

    # Reveal MusicVault and remove the splash at the same moment.
    splash.close()
    if not has_geometry:
        window.showMaximized()
    else:
        window.show()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())
