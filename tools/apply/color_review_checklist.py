from pathlib import Path

PATH = Path("gui/release_detail_page.py")
text = PATH.read_text(encoding="utf-8-sig")

old = '''        self.review_checklist.setStyleSheet(\n            """\n            QLabel {\n                color: #dddddd;\n                background-color: #18181d;\n                border: 1px solid #383842;\n                border-radius: 7px;\n                padding: 9px 12px;\n                font-size: 13px;\n                font-weight: bold;\n            }\n            """\n        )\n'''

new = '''        self.review_checklist.setStyleSheet(\n            """\n            QLabel {\n                color: #f2f2f2;\n                background-color: #18181d;\n                border: 1px solid #383842;\n                border-radius: 7px;\n                padding: 9px 12px;\n                font-size: 13px;\n                font-weight: bold;\n            }\n            """\n        )\n'''

if text.count(old) != 1:
    raise RuntimeError("Checklist style niet uniek gevonden")

text = text.replace(old, new, 1)

start = text.find('    def update_review_checklist(self, data):')
end = text.find('    # ========================================================\n    # LOAD RELEASE', start)

if start < 0 or end < 0:
    raise RuntimeError("update_review_checklist niet gevonden")

new_method = '''    def update_review_checklist(self, data):\n\n        if not hasattr(self, "review_checklist"):\n            return\n\n        release = data.get("release", {})\n        tracks = data.get("tracks", []) or []\n\n        checks = []\n\n        def add_check(label, ok, detail=""):\n\n            mark = "✓" if ok else "✗"\n            suffix = f" ({detail})" if detail else ""\n            color = "#7CFF9B" if ok else "#FF9A9A"\n\n            checks.append(\n                f'<span style="color:{color};">{mark} {label}{suffix}</span>'\n            )\n\n        add_check(\n            "Artist",\n            bool(str(release["artist"] or "").strip())\n        )\n        add_check(\n            "Titel",\n            bool(str(release["title"] or "").strip())\n        )\n        add_check(\n            "Label",\n            bool(str(release["label"] or "").strip())\n        )\n        add_check(\n            "Catalogus",\n            bool(str(release["catalog"] or "").strip())\n        )\n        add_check(\n            "Jaar",\n            bool(str(release["year"] or "").strip())\n        )\n        add_check(\n            "Kastcode",\n            bool(str(release["storage_code"] or "").strip())\n        )\n        add_check(\n            "Discogs",\n            bool(str(release["discogs"] or "").strip())\n        )\n        add_check(\n            "Cover",\n            bool(str(release["cover"] or "").strip())\n        )\n        add_check(\n            "Tracks",\n            bool(tracks),\n            str(len(tracks))\n        )\n\n        missing_positions = 0\n        missing_titles = 0\n        missing_mp3 = 0\n        positions = set()\n        duplicate_positions = 0\n\n        for track_data in tracks:\n\n            track = track_data["track"]\n            position = str(track["position"] or "").strip().upper()\n\n            if not position:\n                missing_positions += 1\n            elif position in positions:\n                duplicate_positions += 1\n            else:\n                positions.add(position)\n\n            if not str(track["title"] or "").strip():\n                missing_titles += 1\n\n            if not (track_data.get("mp3s", []) or []):\n                missing_mp3 += 1\n\n        add_check(\n            "Trackposities",\n            bool(tracks) and missing_positions == 0 and duplicate_positions == 0\n        )\n        add_check(\n            "Tracktitels",\n            bool(tracks) and missing_titles == 0\n        )\n        add_check(\n            "MP3 koppelingen",\n            bool(tracks) and missing_mp3 == 0\n        )\n\n        self.review_checklist.setText(\n            "&nbsp;&nbsp;&nbsp;".join(checks)\n        )\n'''

text = text[:start] + new_method + '\n\n' + text[end:]
PATH.write_text(text, encoding="utf-8-sig")
print("REVIEW CHECKLIST KLEUREN TOEGEVOEGD")
