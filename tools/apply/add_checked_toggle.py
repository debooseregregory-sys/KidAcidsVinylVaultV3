from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8-sig")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected 1 occurrence, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# ============================================================
# DATABASE: expose checked status
# ============================================================

db = ROOT / "database" / "database.py"

# Make sure the column exists on databases that do not have it yet.
text = db.read_text(encoding="utf-8-sig")

migration_marker = '''        _ensure_column(
            connection,
            "releases",
            "notes",
            "TEXT DEFAULT ''"
        )
'''

migration_add = '''        _ensure_column(
            connection,
            "releases",
            "notes",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "checked",
            "INTEGER DEFAULT 0"
        )
'''

if '"checked",\n            "INTEGER DEFAULT 0"' not in text:
    replace_once(db, migration_marker, migration_add)

# Release detail SELECT must expose checked.
replace_once(
    db,
    '''                notes,
                storage_code
            FROM releases
''',
    '''                notes,
                storage_code,
                checked
            FROM releases
'''
)

# Release library/search rows must expose checked.
old_library = '''                r.notes,
                r.storage_code,

                COUNT(DISTINCT t.id) AS track_count,
'''
new_library = '''                r.notes,
                r.storage_code,
                r.checked,

                COUNT(DISTINCT t.id) AS track_count,
'''

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
    '''        self.checked_button = QPushButton(
            "[ ✓ KLAAR ]"
        )
''',
    '''        self.checked_button = QPushButton(
            "[ KLAAR - MARKEREN ]"
        )
'''
)

replace_once(
    detail,
    '''        self.checked_button.clicked.connect(
            self.mark_release_checked
        )
''',
    '''        self.checked_button.clicked.connect(
            self.toggle_release_checked
        )
'''
)

replace_once(
    detail,
    '''        self.info_label.setText(
            "  -  ".join(
                info
            )
        )

        # ----------------------------------------------------
        # EDITOR
''',
    '''        self.info_label.setText(
            "  -  ".join(
                info
            )
        )

        self.update_checked_button(
            release
        )

        # ----------------------------------------------------
        # EDITOR
'''
)

# Replace the old one-way function with a toggle.
start = '''    # ========================================================
    # MARK RELEASE AS CHECKED
    # ========================================================

    def mark_release_checked(self):
'''
end = '''    # ========================================================
    # SAVE RELEASE
    # ========================================================
'''

text = detail.read_text(encoding="utf-8-sig")
start_pos = text.find(start)
end_pos = text.find(end, start_pos)

if start_pos < 0 or end_pos < 0:
    raise RuntimeError("Could not find KLAAR function block")

new_block = '''    # ========================================================
    # KLAAR STATUS
    # ========================================================

    def update_checked_button(
        self,
        release
    ):

        checked = False

        try:
            checked = int(
                release["checked"] or 0
            ) == 1
        except Exception:
            checked = False

        if checked:

            self.checked_button.setText(
                "[ ✓ KLAAR - TERUGZETTEN ]"
            )

        else:

            self.checked_button.setText(
                "[ KLAAR - MARKEREN ]"
            )

    def toggle_release_checked(self):

        if self.release_id is None:
            return

        try:

            from database.database import get_connection

            connection = get_connection()

            try:

                current = connection.execute(
                    """
                    SELECT checked
                    FROM releases
                    WHERE id = ?
                    """,
                    (
                        self.release_id,
                    )
                ).fetchone()

                current_checked = (
                    int(current["checked"] or 0) == 1
                    if current
                    else False
                )

                new_value = 0 if current_checked else 1

                connection.execute(
                    """
                    UPDATE releases
                    SET checked = ?
                    WHERE id = ?
                    """,
                    (
                        new_value,
                        self.release_id,
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
                    "De KLAAR-status kon niet worden opgeslagen.\n\n"
                    f"{error}"
                )
            )

            return

        data = get_release_details(
            self.release_id
        )

        if data:
            self.update_checked_button(
                data["release"]
            )

        if new_value:

            QMessageBox.information(
                self,
                "KLAAR",
                "Deze release is als KLAAR gemarkeerd."
            )

        else:

            QMessageBox.information(
                self,
                "KLAAR",
                "Deze release is teruggezet naar NIET KLAAR."
            )

'''

detail.write_text(
    text[:start_pos] + new_block + text[end_pos:],
    encoding="utf-8"
)

print("KLAAR-status is nu vanuit het programma aan/uit te zetten.")
print("Start daarna: python run_v3.py")
