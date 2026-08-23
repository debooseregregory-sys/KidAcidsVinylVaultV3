import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTimer

from gui.cd_mode import install_cd_mode
from gui.startup_splash import StartupSplash


install_cd_mode()


if __name__ == "__main__":
    # Start MusicVault in the SAME process as the splash. This removes the
    # extra Python-process startup and the visible hand-off delay.
    app = QApplication(sys.argv)
    app.setApplicationName("Kid Acid's MusicVault")
    app.setApplicationDisplayName("Kid Acid's MusicVault")
    app.setStyle("Fusion")

    splash = StartupSplash(duration=3200)
    splash.show()
    app.processEvents()

    # Build the real main window while the splash is already visible.
    # There is no subprocess and therefore no second Python startup.
    import gui.main_window as main_window

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

    # MusicVault is ready. Keep the splash visible briefly so the transition
    # feels intentional, without adding meaningful startup work or delay.
    def finish_startup():
        splash.close()
        window.raise_()
        window.activateWindow()

    QTimer.singleShot(1200, finish_startup)

    sys.exit(app.exec())
