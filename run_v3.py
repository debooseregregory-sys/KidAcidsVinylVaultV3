import sys

from PySide6.QtCore import QSettings, QTimer
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

    import gui.main_window as main_window

    window = main_window.VinylVaultWindow()

    settings = QSettings("Kid Acid", "MusicVault")
    has_geometry = (
        settings.value("window_geometry") is not None
        and settings.value("remember_window_state", True, type=bool)
    )

    # Prepare the main window but keep it completely hidden while the splash
    # remains visible. Do not block Qt with time.sleep(): the splash animation
    # must continue running normally.
    if not has_geometry:
        window.showMaximized()
        window.hide()
    else:
        window.show()
        window.hide()

    app.processEvents()

    def reveal_application():
        splash.close()
        if not has_geometry:
            window.showMaximized()
        else:
            window.show()
        window.raise_()
        window.activateWindow()

    # Keep the splash visible for a real minimum of 5 seconds while Qt's
    # event loop continues to run. When the timer fires, reveal MusicVault
    # immediately with no additional delay.
    QTimer.singleShot(5000, reveal_application)

    sys.exit(app.exec())
