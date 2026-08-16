from pathlib import Path

path = Path("gui/release_detail_page.py")

text = path.read_text(encoding="utf-8")

# ============================================================
# IMPORTS
# ============================================================

text = text.replace(
    "from PySide6.QtCore import Signal",
    "from PySide6.QtCore import Signal, Qt"
)

text = text.replace(
    "from PySide6.QtWidgets import (",
    "from PySide6.QtGui import QPixmap\n"
    "from PySide6.QtWidgets import ("
)

# ============================================================
# TRACK DELETE
# ============================================================

old = '''    def delete_track(self):

        from database.database import (
            get_connection
        )

        connection = get_connection()

        try:

            connection.execute(
                """
                DELETE FROM track_mp3
                WHERE track_id = ?
                """,
                (self.track["id"],)
            )

            connection.execute(
                """
                DELETE FROM tracks
                WHERE id = ?
                """,
                (self.track["id"],)
            )

            connection.commit()

        except Exception as exc:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Track verwijderen mislukt",
                str(exc)
            )

            return

        finally:

            connection.close()

        self.track_changed.emit()
'''

new = '''    def delete_track(self):

        reply = QMessageBox.question(
            self,
            "Track verwijderen",
            (
                "Deze track definitief verwijderen?\\n\\n"
                f"{self.track["position"]} - "
                f"{self.track["title"]}\\n\\n"
                "De MP3-koppelingen van deze track "
                "worden eveneens verwijderd."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        from database.database import get_connection

        connection = get_connection()

        try:

            connection.execute(
                """
                DELETE FROM track_mp3
                WHERE track_id = ?
                """,
                (self.track["id"],)
            )

            connection.execute(
                """
                DELETE FROM tracks
                WHERE id = ?
                """,
                (self.track["id"],)
            )

            connection.commit()

        except Exception as exc:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Track verwijderen mislukt",
                f"De track kon niet worden verwijderd.\\n\\n{exc}"
            )

            return

        finally:

            connection.close()

        # Signaal naar ReleaseDetailPage.
        # Die laadt de release opnieuw waardoor de
        # verwijderde track onmiddellijk verdwijnt.
        self.track_changed.emit()
'''

if old in text:
    text = text.replace(old, new)
else:
    print("WAARSCHUWING: bestaande delete_track() wijkt af.")
    print("Deze functie is NIET aangepast.")

# ============================================================
# COVER PREVIEW
# ============================================================

marker = '''    # ========================================================
    # CHOOSE COVER
    # ========================================================
'''

preview = '''    # ========================================================
    # COVER PREVIEW
    # ========================================================

    def update_cover_preview(self):

        if not hasattr(self, "cover_preview"):
            return

        filename = (
            self.edit_cover.text()
            .strip()
        )

        if not filename:

            self.cover_preview.clear()

            self.cover_preview.setText(
                "GEEN COVER"
            )

            return

        pixmap = QPixmap()

        # Lokale afbeelding
        if pixmap.load(filename):

            self.cover_preview.setPixmap(
                pixmap.scaled(
                    self.cover_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

            return

        self.cover_preview.clear()

        self.cover_preview.setText(
            "COVER NIET GEVONDEN"
        )

    # ========================================================
'''

if "def update_cover_preview" not in text:

    if marker in text:
        text = text.replace(
            marker,
            preview + marker
        )
    else:
        print("WAARSCHUWING: CHOOSE COVER niet gevonden.")

# ============================================================
# COVER PREVIEW WIDGET
# ============================================================

marker = '''        form.addRow(
            "Cover:",
            cover_row
        )
'''

replacement = '''        form.addRow(
            "Cover:",
            cover_row
        )

        # ----------------------------------------------------
        # COVER PREVIEW
        # ----------------------------------------------------

        self.cover_preview = QLabel(
            "GEEN COVER"
        )

        self.cover_preview.setFixedSize(
            180,
            180
        )

        self.cover_preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.cover_preview.setStyleSheet(
            """
            QLabel {
                background-color: #202020;
                color: #777777;
                border: 1px solid #444444;
                border-radius: 6px;
            }
            """
        )

        form.addRow(
            "Preview:",
            self.cover_preview
        )
'''

if 'self.cover_preview = QLabel' not in text:

    if marker in text:
        text = text.replace(
            marker,
            replacement
        )
    else:
        print("WAARSCHUWING: Cover-row niet gevonden.")

# ============================================================
# UPDATE PREVIEW AFTER FILL_EDITOR
# ============================================================

needle = '''        self.edit_cover.setText(
            str(
                release["cover"]
                or ""
            )
        )
'''

if needle in text and "        self.update_cover_preview()" not in text:
    text = text.replace(
        needle,
        needle + "\n        self.update_cover_preview()\n",
        1
    )

# ============================================================
# UPDATE PREVIEW AFTER CHOOSE COVER
# ============================================================

needle = '''        self.edit_cover.setText(
            filename
        )
'''

if needle in text:

    replacement = '''        self.edit_cover.setText(
            filename
        )

        self.update_cover_preview()
'''

    text = text.replace(
        needle,
        replacement,
        1
    )

# ============================================================
# UPDATE PREVIEW AFTER DISCOGS COVER
# ============================================================

needle = '''            self.edit_cover.setText(
                data["cover"]
            )
'''

if needle in text:

    replacement = '''            self.edit_cover.setText(
                data["cover"]
            )

            self.update_cover_preview()
'''

    text = text.replace(
        needle,
        replacement,
        1
    )

# ============================================================
# SAVE
# ============================================================

path.write_text(
    text,
    encoding="utf-8"
)

print()
print("==============================================")
print(" RELEASE DETAIL PAGE PATCH")
print("==============================================")
print("Klaar.")
print()
print("Aangepast:")
print("- Track verwijderen")
print("- Track direct uit editor verwijderen")
print("- Cover preview")
print("- Cover kiezen preview")
print("- Discogs cover preview")
print()