from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "gui" / "mp3_showcase_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

old = '''        self.list = QListWidget()\n        self.list.setMinimumWidth(360)\n        self.list.setMaximumWidth(380)\n        self.list.currentRowChanged.connect(self.select_index)\n        body.addWidget(self.list)'''
new = '''        list_panel = QWidget()\n        list_layout = QVBoxLayout(list_panel)\n        list_layout.setContentsMargins(0, 0, 0, 0)\n        list_layout.setSpacing(0)\n\n        header = QWidget()\n        header_layout = QHBoxLayout(header)\n        header_layout.setContentsMargins(14, 8, 14, 8)\n        header_layout.setSpacing(12)\n        artist_header = QLabel("ARTIEST")\n        track_header = QLabel("TRACK")\n        artist_header.setMinimumWidth(220)\n        artist_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)\n        track_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)\n        artist_header.setStyleSheet("color:#8f8b96;font-size:10px;font-weight:900;letter-spacing:1px;")\n        track_header.setStyleSheet("color:#8f8b96;font-size:10px;font-weight:900;letter-spacing:1px;")\n        header_layout.addWidget(artist_header, 5)\n        header_layout.addWidget(track_header, 6)\n        list_layout.addWidget(header)\n\n        self.list = QListWidget()\n        self.list.setMinimumWidth(560)\n        self.list.setMaximumWidth(720)\n        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)\n        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)\n        self.list.currentRowChanged.connect(self.select_index)\n        list_layout.addWidget(self.list, 1)\n        body.addWidget(list_panel, 1)'''

if old not in text:
    raise SystemExit("List layout block not found; no changes made.")
text = text.replace(old, new, 1)

old = '''            name = Path(str(row[0])).name\n            artist = str(row[1] or "").strip()\n            title = str(row[2] or "").strip()\n            text = (\n                f"{artist} - {title}".strip(" -")\n                if artist or title\n                else name\n            )\n            item = QListWidgetItem(text)\n            item.setToolTip(str(row[0]))\n            self.list.addItem(item)'''
new = '''            name = Path(str(row[0])).name\n            artist = str(row[1] or "").strip() or "Onbekende artiest"\n            title = str(row[2] or "").strip() or name\n\n            item = QListWidgetItem()\n            item.setToolTip(str(row[0]))\n\n            item_widget = QWidget()\n            item_layout = QHBoxLayout(item_widget)\n            item_layout.setContentsMargins(14, 8, 14, 8)\n            item_layout.setSpacing(12)\n\n            artist_label = QLabel(artist)\n            artist_label.setWordWrap(False)\n            artist_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)\n            artist_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)\n            artist_label.setStyleSheet("color:#d8d4dc;font-weight:700;")\n\n            title_label = QLabel(title)\n            title_label.setWordWrap(False)\n            title_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)\n            title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)\n            title_label.setStyleSheet("color:#ffffff;")\n\n            item_layout.addWidget(artist_label, 5)\n            item_layout.addWidget(title_label, 6)\n            self.list.addItem(item)\n            item.setSizeHint(item_widget.sizeHint())\n            self.list.setItemWidget(item, item_widget)'''

if old not in text:
    raise SystemExit("List population block not found; no changes made.")
text = text.replace(old, new, 1)

old = '''            QListWidget{background:#0f0f14;}\n            QListWidget::item{\n                padding:8px;\n                border-bottom:1px solid #24242d;\n            }'''
new = '''            QListWidget{background:#0f0f14;}\n            QListWidget::item{\n                padding:0;\n                border-bottom:1px solid #24242d;\n            }'''
if old in text:
    text = text.replace(old, new, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 Showcase lijst aangepast: ARTIEST en TRACK zijn nu aparte, brede kolommen.")
