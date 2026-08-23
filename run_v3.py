import sys

from PySide6.QtWidgets import QApplication

from gui.cd_mode import install_cd_mode
from gui.startup_splash import StartupSplash


install_cd_mode()


if __name__ == "__main__":
    # Start MusicVault in the SAME process as the splash. The splash stays
    # visible until the real main window has finished loading.
    app = QApplication(sys.argv)
    app.setApplicationName("Kid Acid's MusicVault")
    app.setApplicationDisplayName("Kid Acid's MusicVault")
    app.setStyle("Fusion")

    splash = StartupSplash(duration=None)
    splash.show()
    app.processEvents()

    # Build the real main window while the splash is already visible.
    # There is no subprocess and therefore no second Python startup.
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

    # The main window is ready. Only now remove the splash.
    splash.close()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())
