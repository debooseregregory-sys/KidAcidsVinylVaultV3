from pathlib import Path


PATH = Path("gui/release_detail_page.py")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count == 0:
        raise RuntimeError(f"{label}: patroon niet gevonden")
    if count > 1:
        raise RuntimeError(f"{label}: verwacht 1 patroon, gevonden {count}")
    return text.replace(old, new, 1)


text = PATH.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# Werk uitsluitend binnen ReleaseDetailPage.
# Dit bestand bevat meerdere build_ui()-methodes.
# ------------------------------------------------------------

marker = "class ReleaseDetailPage(QWidget):"

if marker not in text:
    raise RuntimeError("ReleaseDetailPage: class niet gevonden")

prefix, detail = text.split(marker, 1)

method = '''    # ========================================================
    # NEXT NIET-KLAAR RELEASE
    # ========================================================

    def go_next_todo_release(self):

        if self.navigation_index < 0:
            return

        if not self.navigation_ids:
            return

        try:

            from database.database import get_connection

            connection = get_connection()

            try:

                for index in range(
                    self.navigation_index + 1,
                    len(self.navigation_ids)
                ):

                    candidate_id = self.navigation_ids[index]

                    row = connection.execute(
                        "SELECT checked FROM releases WHERE id = ?",
                        (candidate_id,)
                    ).fetchone()

                    checked = int(row[0] or 0) if row else 0

                    if checked == 0:

                        self.navigation_index = index

                        self.load_release(
                            candidate_id
                        )

                        self.update_navigation_buttons()

                        return

            finally:

                connection.close()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Volgende niet-klaar release",
                (
                    "De volgende niet-klaar release kon niet worden geopend.\\n\\n"
                    f"{error}"
                )
            )

'''

if "def go_next_todo_release(self):" not in detail:
    detail = replace_once(
        detail,
        "    def build_ui(self):\n",
        method + "    def build_ui(self):\n",
        "methode next niet-klaar"
    )

button_block = '''        self.next_todo_button = QPushButton(
            "[ VOLGENDE NIET-KLAAR ▶ ]"
        )

        self.next_todo_button.setMinimumHeight(
            38
        )

        self.next_todo_button.clicked.connect(
            self.go_next_todo_release
        )

        top.addWidget(
            self.next_todo_button
        )

'''

if "self.next_todo_button = QPushButton(" not in detail:
    detail = replace_once(
        detail,
        '''        top.addWidget(
            self.next_button
        )

        top.addStretch()
''',
        '''        top.addWidget(
            self.next_button
        )

''' + button_block + '''        top.addStretch()
''',
        "knop volgende niet-klaar"
    )

PATH.write_text(prefix + marker + detail, encoding="utf-8-sig")

print("VOLGENDE NIET-KLAAR NAVIGATIE TOEGEVOEGD")
