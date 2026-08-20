# ============================================================
# KID ACID'S VINYLVAULT V3
# ONE-COMMAND CD MODULE INSTALLER
# ============================================================

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def run(script):
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script)],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    run("enable_cd_library.py")
    run("import_cd_collection.py")
    print("\nCD MODULE KLAAR.")
    print("Start VinylVault opnieuw om CD Library in de linkerzijbalk te gebruiken.")
