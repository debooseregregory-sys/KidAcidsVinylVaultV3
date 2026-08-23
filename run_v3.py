import os
import subprocess
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui.cd_mode import install_cd_mode
from gui.startup_splash import StartupSplash


install_cd_mode()


if __name__ == "__main__":
    # The normal application remains completely untouched.  The splash is a
    # short announcement that hands off to the existing launcher afterwards.
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
            app.quit()

        QTimer.singleShot(3700, launch_vault)
        sys.exit(app.exec())
