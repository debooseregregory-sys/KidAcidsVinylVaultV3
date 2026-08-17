from pathlib import Path

PATH = Path("gui/release_detail_page.py")

text = PATH.read_text(encoding="utf-8-sig")

start = text.find("    # ========================================================\n    # MARK RELEASE AS CHECKED\n    # ========================================================\n")
end = text.find("    # ========================================================\n    # UPDATE KLAAR BUTTON\n    # ========================================================\n", start)

if start < 0 or end < 0:
    raise RuntimeError("KLAAR-blok niet gevonden")

new_block = '''    # ========================================================
    # VALIDATE RELEASE BEFORE CHECKED
    # ========================================================

    def validate_release_before_checked(self):

        data = get_release_details(
            self.release_id
        )

        if not data:
            return [
                "Releasegegevens konden niet worden geladen."
            ]

        release = data["release"]
        tracks = data.get("tracks", []) or []
        missing = []

        required_release_fields = [
            ("Artist", "artist"),
            ("Titel", "title"),
            ("Label", "label"),
            ("Catalogusnummer", "catalog"),
            ("Jaar", "year"),
            ("Kastcode", "storage_code"),
            ("Discogs", "discogs"),
            ("Cover", "cover"),
        ]

        for label, key in required_release_fields:
            value = release[key]
            if value is None or not str(value).strip():
                missing.append(
                    f"{label} ontbreekt"
                )

        if not tracks:
            missing.append(
                "Geen tracks aanwezig"
            )

        for index, track_data in enumerate(tracks, 1):

            track = track_data["track"]
            position = str(
                track["position"] or ""
            ).strip()
            title = str(
                track["title"] or ""
            ).strip()
            mp3s = track_data.get(
                "mp3s", []
            ) or []

            track_name = (
                position
                or f"Track {index}"
            )

            if not position:
                missing.append(
                    f"{track_name}: positie ontbreekt"
                )

            if not title:
                missing.append(
                    f"{track_name}: titel ontbreekt"
                )

            if not mp3s:
                missing.append(
                    f"{track_name}: geen MP3 gekoppeld"
                )

        return missing

    # ========================================================
    # MARK RELEASE AS CHECKED
    # ========================================================

    def mark_release_checked(self):

        if self.release_id is None:
            return

        try:

            from database.database import get_connection

            connection = get_connection()

            try:

                row = connection.execute(
                    "SELECT checked FROM releases WHERE id = ?",
                    (self.release_id,)
                ).fetchone()

                current = int(
                    row[0] or 0
                ) if row else 0

                # Een reeds gecontroleerde release mag altijd
                # weer teruggezet worden.
                if current:
                    new_value = 0

                else:
                    missing = self.validate_release_before_checked()

                    if missing:

                        details = "\\n".join(
                            f"✗ {item}"
                            for item in missing
                        )

                        QMessageBox.warning(
                            self,
                            "RELEASE NIET COMPLEET",
                            (
                                "Deze release kan nog niet als KLAAR "
                                "worden gemarkeerd.\\n\\n"
                                f"{details}\\n\\n"
                                "Vul de ontbrekende gegevens eerst in."
                            )
                        )

                        return

                    new_value = 1

                connection.execute(
                    "UPDATE releases SET checked = ? WHERE id = ?",
                    (
                        new_value,
                        self.release_id
                    )
                )

                connection.commit()

            finally:

                connection.close()

        except Exception as error:

            QMessageBox.critical(
                self,
                "KLAAR opslaan mislukt",
                (
                    "De KLAAR-status kon niet worden opgeslagen.\\n\\n"
                    f"{error}"
                )
            )
            return

        self.update_checked_button(
            new_value
        )

'''

text = text[:start] + new_block + text[end:]
PATH.write_text(text, encoding="utf-8-sig")
print("KLAAR-CONTROLE TOEGEVOEGD")
