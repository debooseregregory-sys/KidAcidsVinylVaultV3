from pathlib import Path

PATH = Path("gui/release_detail_page.py")
text = PATH.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# Add a visible checklist widget directly after info_label.
# ------------------------------------------------------------

ui_marker = '''        main_layout.addWidget(\n            self.info_label\n        )\n'''

ui_insert = '''        main_layout.addWidget(\n            self.info_label\n        )\n\n        # ====================================================\n        # REVIEW CHECKLIST\n        # ====================================================\n\n        self.review_checklist = QLabel()\n\n        self.review_checklist.setWordWrap(\n            True\n        )\n\n        self.review_checklist.setMinimumHeight(\n            38\n        )\n\n        self.review_checklist.setStyleSheet(\n            """\n            QLabel {\n                color: #dddddd;\n                background-color: #18181d;\n                border: 1px solid #383842;\n                border-radius: 7px;\n                padding: 9px 12px;\n                font-size: 13px;\n                font-weight: bold;\n            }\n            """\n        )\n\n        main_layout.addWidget(\n            self.review_checklist\n        )\n'''

if "self.review_checklist = QLabel()" not in text:
    if text.count(ui_marker) != 1:
        raise RuntimeError(
            f"review checklist UI marker: expected 1, found {text.count(ui_marker)}"
        )
    text = text.replace(ui_marker, ui_insert, 1)

# ------------------------------------------------------------
# Add checklist updater before load_release.
# ------------------------------------------------------------

method_marker = '''    # ========================================================\n    # LOAD RELEASE\n    # ========================================================\n'''

method_insert = '''    # ========================================================\n    # REVIEW CHECKLIST\n    # ========================================================\n\n    def update_review_checklist(self, data):\n\n        if not hasattr(self, "review_checklist"):\n            return\n\n        release = data.get("release", {})\n        tracks = data.get("tracks", []) or []\n\n        checks = []\n\n        def add_check(label, ok):\n            checks.append(\n                f"✓ {label}" if ok else f"✗ {label}"\n            )\n\n        add_check(\n            "Artist",\n            bool(str(release["artist"] or "").strip())\n        )\n        add_check(\n            "Titel",\n            bool(str(release["title"] or "").strip())\n        )\n        add_check(\n            "Label",\n            bool(str(release["label"] or "").strip())\n        )\n        add_check(\n            "Catalogus",\n            bool(str(release["catalog"] or "").strip())\n        )\n        add_check(\n            "Jaar",\n            bool(str(release["year"] or "").strip())\n        )\n        add_check(\n            "Kastcode",\n            bool(str(release["storage_code"] or "").strip())\n        )\n        add_check(\n            "Discogs",\n            bool(str(release["discogs"] or "").strip())\n        )\n        add_check(\n            "Cover",\n            bool(str(release["cover"] or "").strip())\n        )\n        add_check(\n            f"Tracks ({len(tracks)})",\n            bool(tracks)\n        )\n\n        missing_track_positions = 0\n        missing_track_titles = 0\n        missing_mp3 = 0\n\n        for track_data in tracks:\n            track = track_data["track"]\n            if not str(track["position"] or "").strip():\n                missing_track_positions += 1\n            if not str(track["title"] or "").strip():\n                missing_track_titles += 1\n            if not (track_data.get("mp3s", []) or []):\n                missing_mp3 += 1\n\n        add_check(\n            "Trackposities",\n            missing_track_positions == 0 and bool(tracks)\n        )\n        add_check(\n            "Tracktitels",\n            missing_track_titles == 0 and bool(tracks)\n        )\n        add_check(\n            "MP3 koppelingen",\n            missing_mp3 == 0 and bool(tracks)\n        )\n\n        self.review_checklist.setText(\n            "    ".join(checks)\n        )\n\n    # ========================================================\n    # LOAD RELEASE\n    # ========================================================\n'''

if "def update_review_checklist(self, data):" not in text:
    if text.count(method_marker) != 1:
        raise RuntimeError(
            f"review checklist method marker: expected 1, found {text.count(method_marker)}"
        )
    text = text.replace(method_marker, method_insert, 1)

# ------------------------------------------------------------
# Refresh checklist whenever a release is loaded.
# ------------------------------------------------------------

load_marker = '''        release = data["release"]\n\n'''
load_insert = '''        release = data["release"]\n\n        self.update_review_checklist(\n            data\n        )\n\n'''

if "self.update_review_checklist(" not in text:
    if text.count(load_marker) != 1:
        raise RuntimeError(
            f"review checklist load marker: expected 1, found {text.count(load_marker)}"
        )
    text = text.replace(load_marker, load_insert, 1)

PATH.write_text(text, encoding="utf-8-sig")
print("ZICHTBARE REVIEW CHECKLIST TOEGEVOEGD")
