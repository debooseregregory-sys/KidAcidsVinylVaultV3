# ============================================================
# KID ACID'S VINYLVAULT V3
# KLAAR AUTO-SAVE
#
# Ensures the KLAAR button persists the current release editor
# fields before the existing checked/status handler runs.
# ============================================================

from __future__ import annotations

from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QApplication, QAbstractButton


_FILTER = None


def _find_release_page(widget):
    current = widget

    while current is not None:
        if (
            hasattr(current, "release_id")
            and hasattr(current, "edit_artist")
            and hasattr(current, "edit_title")
            and hasattr(current, "save_release")
        ):
            return current

        parent_method = getattr(current, "parent", None)
        current = parent_method() if callable(parent_method) else None

    return None


def save_current_release_editor(page):
    """Persist the current release editor fields without leaving the page."""

    if page is None or page.release_id is None:
        return False

    artist = page.edit_artist.text().strip()
    title = page.edit_title.text().strip()
    label = page.edit_label.text().strip()
    catalog = page.edit_catalog.text().strip()
    year_text = page.edit_year.text().strip()
    genre = page.edit_genre.text().strip()
    storage_code = page.edit_storage.text().strip()
    discogs = page.edit_discogs.text().strip()
    discogs_link = page.edit_discogs_link.text().strip()
    cover = page.edit_cover.text().strip()
    notes = page.edit_notes.text().strip()

    if not artist:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(
            page,
            "Opslaan",
            "Artist mag niet leeg zijn.",
        )
        return False

    # A release title may legitimately be empty in the existing database.
    # KLAAR must still persist all other fields in that case.
    year = None

    if year_text:
        try:
            year = int(year_text)
        except ValueError:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                page,
                "Ongeldig jaar",
                "Het jaar moet een getal zijn.",
            )
            return False

        if year < 1800 or year > 2100:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                page,
                "Ongeldig jaar",
                "Vul een geldig jaar in.",
            )
            return False

    try:
        from database.database import update_release

        update_release(
            release_id=page.release_id,
            artist=artist,
            title=title,
            label=label,
            catalog=catalog,
            year=year,
            genre=genre,
            storage_code=storage_code,
            discogs=discogs,
            discogs_link=discogs_link,
            cover=cover,
            notes=notes,
        )

    except Exception as exc:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            page,
            "KLAAR opslaan mislukt",
            "De releasegegevens konden niet worden opgeslagen.\n\n"
            f"{exc}",
        )
        return False

    try:
        page.discogs_data = None
        page.discogs_take_button.setEnabled(False)
    except Exception:
        pass

    return True


class KlaarAutoSaveFilter(QObject):
    def eventFilter(self, watched, event):
        if isinstance(watched, QAbstractButton):
            text = str(watched.text() or "").upper()

            if "KLAAR" in text:
                should_save = False

                if event.type() == QEvent.Type.MouseButtonRelease:
                    should_save = (
                        event.button() == Qt.MouseButton.LeftButton
                    )

                elif event.type() == QEvent.Type.KeyRelease:
                    should_save = event.key() in (
                        Qt.Key.Key_Return,
                        Qt.Key.Key_Enter,
                        Qt.Key.Key_Space,
                    )

                if should_save:
                    page = _find_release_page(watched)

                    if page is not None:
                        if not save_current_release_editor(page):
                            # Stop the click when saving failed so the
                            # checked status cannot be changed independently.
                            return True

        return super().eventFilter(watched, event)


def install_klaar_autosave():
    global _FILTER

    app = QApplication.instance()

    if app is None:
        return False

    if _FILTER is None:
        _FILTER = KlaarAutoSaveFilter(app)
        app.installEventFilter(_FILTER)

    return True
