from pathlib import Path

PATH = Path("gui/release_detail_page.py")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: verwacht 1 patroon, gevonden {count}")
    return text.replace(old, new, 1)


text = PATH.read_text(encoding="utf-8-sig")

method = '''    # ========================================================
    # REVIEW STATUS
    # ========================================================

    def update_review_status(self, release, tracks):

        storage_ok = bool(
            str(release["storage_code"] or "").strip()
        )

        discogs_ok = bool(
            str(release["discogs"] or "").strip()
        )

        track_count = len(tracks or [])

        mp3_count = 0

        for track_data in tracks or []:

            mp3_count += len(
                track_data.get("mp3s", []) or []
            )

        mp3_ok = mp3_count > 0

        checked = bool(
            int(release["checked"] or 0)
        )

        def status_text(name, ok, detail=""):

            mark = "✓" if ok else "✗"

            suffix = f"  {detail}" if detail else ""

            return f"{mark} {name}{suffix}"

        self.review_status_label.setText(
            "    ".join(
                [
                    status_text("KASTCODE", storage_ok),
                    status_text("MP3", mp3_ok, str(mp3_count)),
                    status_text("DISCOGS", discogs_ok),
                    status_text("TRACKS", track_count > 0, str(track_count)),
                    status_text("KLAAR", checked),
                ]
            )
        )

    def refresh_review_status(self):

        if self.release_id is None:
            return

        data = get_release_details(
            self.release_id
        )

        if not data:
            return

        self.update_review_status(
            data["release"],
            data["tracks"]
        )

'''

if "def update_review_status(self, release, tracks):" not in text:
    text = replace_once(
        text,
        "    def build_ui(self):\n",
        method + "    def build_ui(self):\n",
        "review status methode"
    )

ui_block = '''        self.review_status_label = QLabel(
            "REVIEW STATUS"
        )

        self.review_status_label.setWordWrap(
            True
        )

        self.review_status_label.setMinimumHeight(
            38
        )

        self.review_status_label.setStyleSheet(
            """
            QLabel {
                color: #dddddd;
                background-color: #18181d;
                border: 1px solid #383842;
                border-radius: 7px;
                padding: 9px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            """
        )

        main_layout.addWidget(
            self.review_status_label
        )

'''

if "self.review_status_label = QLabel(" not in text:
    text = replace_once(
        text,
        "        main_layout.addWidget(\n            self.info_label\n        )\n",
        "        main_layout.addWidget(\n            self.info_label\n        )\n\n" + ui_block,
        "review status UI"
    )

load_anchor = '''        self.info_label.setText(
            "  -  ".join(
                info
            )
        )

'''

if "        self.update_review_status(\n            release,\n            data[\"tracks\"]" not in text:
    text = replace_once(
        text,
        load_anchor,
        load_anchor + "        self.update_review_status(\n            release,\n            data[\"tracks\"]\n        )\n\n",
        "review status laden"
    )

checked_anchor = "        self.update_checked_button(new_value)\n"

if "        self.refresh_review_status()\n" not in text:
    text = replace_once(
        text,
        checked_anchor,
        checked_anchor + "        self.refresh_review_status()\n",
        "review status na klaar"
    )

PATH.write_text(text, encoding="utf-8-sig")
print("REVIEW STATUS BAR TOEGEVOEGD")
