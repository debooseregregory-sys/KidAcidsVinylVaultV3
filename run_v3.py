import os
import subprocess
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui.cd_mode import install_cd_mode
from gui.startup_splash import StartupSplash


install_cd_mode()


if __name__ == "__main__":
    # The normal application remains completely untouched. The main window
    # is started while the splash is still visible, so there is no dead time
    # between the splash disappearing and MusicVault appearing.
    if "--no-splash" in sys.argv:
        import gui.main_window as main_window
        main_window.main()
    else:
        app = QApplication(sys.argv)
        app.setApplicationName("Kid Acid's MusicVault")
        app.setApplicationDisplayName("Kid Acid's MusicVault")
        app.setStyle("Fusion")

        splash = StartupSplash(duration=3200)
        splash.show()

        def launch_vault():
            subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "--no-splash"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )

        # Start loading MusicVault before the splash finishes. The splash
        # remains on top during the hand-off, eliminating the visible gap.
        QTimer.singleShot(2400, launch_vault)

        # Keep the splash process alive until its normal animation/fade ends.
        QTimer.singleShot(3700, app.quit)
        sys.exit(app.exec())
