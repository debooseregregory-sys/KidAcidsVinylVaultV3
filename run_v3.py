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

    # Keep the splash visible for at least 5 seconds before the main window
    # is opened. The main window is then shown immediately and the splash
    # disappears at the same moment.
    splash_started = time.monotonic()

    import gui.main_window as main_window
    from PySide6.QtCore import QSettings

    window = main_window.VinylVaultWindow()

    settings = QSettings("Kid Acid", "MusicVault")
    has_geometry = (
        settings.value("window_geometry") is not None
        and settings.value("remember_window_state", True, type=bool)
    )

    if not has_geometry:
        window.showMaximized()
    else:
        window.show()

    app.processEvents()

    # Never show the main window before the minimum splash time has elapsed.
    remaining = 5.0 - (time.monotonic() - splash_started)
    if remaining > 0:
        time.sleep(remaining)

    # The main window is ready. Close the splash and reveal MusicVault
    # immediately, with no fade-out delay.
    splash.close()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())
