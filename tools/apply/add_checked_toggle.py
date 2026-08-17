from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 occurrence, found {count}")
    path.write_text(text.replace(old, new), encoding="utf-8")


# ============================================================
# DATABASE: expose checked status
# ============================================================

db = ROOT / "database" / "database.py"

replace_once(
    db,
    """                notes,\n                storage_code\n            FROM releases\n""",
    """                notes,\n                storage_code,\n                checked\n            FROM releases\n""",
)

# Expose checked in the release-library rows as well.
old_library = """                r.notes,\n                r.storage_code,\n\n                COUNT(DISTINCT t.id) AS track_count,\n"""
new_library = """                r.notes,\n                r.storage_code,\n                r.checked,\n\n                COUNT(DISTINCT t.id) AS track_count,\n"""

text = db.read_text(encoding="utf-8-sig")
count = text.count(old_library)
if count != 2:
    raise RuntimeError(
        "database.py: expected the library/search SELECT block twice, "
        f"found {count}"
    )

db.write_text(
    text.replace(old_library, new_library),
    encoding="utf-8"
)


# ============================================================
# RELEASE DETAIL: reversible KLAAR button
# ============================================================

detail = ROOT / "gui" / "release_detail_page.py"

replace_once(
    detail,
    """        self.checked_button = QPushButton(\n            "[ ✓ KLAAR ]"\n        )\n""",
    """        self.checked_button = QPushButton(\n            "[ KLAAR - MARKEREN ]"\n        )\n""",
)

replace_once(
    detail,
    """        self.checked_button.clicked.connect(\n            self.mark_release_checked\n        )\n""",
    """        self.checked_button.clicked.connect(\n            self.toggle_release_checked\n        )\n""",
)

replace_once(
    detail,
    """        self.info_label.setText(\n            "  -  ".join(\n                info\n            )\n        )\n\n        # ----------------------------------------------------\n        # EDITOR\n""",
    """        self.info_label.setText(\n            "  -  ".join(\n                info\n            )\n        )\n\n        self.update_checked_button(\n            release\n        )\n\n        # ----------------------------------------------------\n        # EDITOR\n""",
)

# Replace the old one-way function with a toggle.
start = """    # ========================================================\n    # MARK RELEASE AS CHECKED\n    # ========================================================\n\n    def mark_release_checked(self):\n"""
end = """    # ========================================================\n    # SAVE RELEASE\n    # ========================================================\n"""

text = detail.read_text(encoding="utf-8-sig")
start_pos = text.find(start)
end_pos = text.find(end, start_pos)

if start_pos < 0 or end_pos < 0:
    raise RuntimeError("Could not find KLAAR function block")

new_block = """    # ========================================================\n    # KLAAR STATUS\n    # ========================================================\n\n    def update_checked_button(\n        self,\n        release\n    ):\n\n        checked = False\n\n        try:\n            checked = int(\n                release[\"checked\"] or 0\n            ) == 1\n        except Exception:\n            checked = False\n\n        if checked:\n\n            self.checked_button.setText(\n                "[ ✓ KLAAR - TERUGZETTEN ]"\n            )\n\n        else:\n\n            self.checked_button.setText(\n                "[ KLAAR - MARKEREN ]"\n            )\n\n    def toggle_release_checked(self):\n\n        if self.release_id is None:\n            return\n\n        try:\n\n            from database.database import get_connection\n\n            connection = get_connection()\n\n            try:\n\n                current = connection.execute(\n                    """\n                    SELECT checked\n                    FROM releases\n                    WHERE id = ?\n                    """,\n                    (\n                        self.release_id,\n                    )\n                ).fetchone()\n\n                current_checked = (\n                    int(current[\"checked\"] or 0) == 1\n                    if current\n                    else False\n                )\n\n                new_value = 0 if current_checked else 1\n\n                connection.execute(\n                    """\n                    UPDATE releases\n                    SET checked = ?\n                    WHERE id = ?\n                    """,\n                    (\n                        new_value,\n                        self.release_id,\n                    )\n                )\n\n                connection.commit()\n\n            finally:\n                connection.close()\n\n        except Exception as error:\n\n            QMessageBox.critical(\n                self,\n                "KLAAR opslaan mislukt",\n                (\n                    "De KLAAR-status kon niet worden opgeslagen.\\n\\n"\n                    f"{error}"\n                )\n            )\n\n            return\n\n        data = get_release_details(\n            self.release_id\n        )\n\n        if data:\n            self.update_checked_button(\n                data[\"release\"]\n            )\n\n        if new_value:\n\n            QMessageBox.information(\n                self,\n                "KLAAR",\n                "Deze release is als KLAAR gemarkeerd."\n            )\n\n        else:\n\n            QMessageBox.information(\n                self,\n                "KLAAR",\n                "Deze release is teruggezet naar NIET KLAAR."\n            )\n\n"""

detail.write_text(
    text[:start_pos] + new_block + text[end_pos:],
    encoding="utf-8"
)

print("KLAAR-status is nu vanuit het programma aan/uit te zetten.")
print("Start daarna: python run_v3.py")
