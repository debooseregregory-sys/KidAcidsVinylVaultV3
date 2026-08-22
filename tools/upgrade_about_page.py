from pathlib import Path

path = Path("gui/settings_page.py")
text = path.read_text(encoding="utf-8")

start = text.index("    def _about_page(self):")
end = text.index("    def _value_button(self, value):", start)

new_about = '''    def _about_page(self):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(2, 2, 10, 8)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("settingsAboutHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(30, 28, 30, 28)
        hero_layout.setSpacing(6)

        eyebrow = QLabel("ABOUT MUSICVAULT")
        eyebrow.setObjectName("settingsAboutSmall")
        hero_layout.addWidget(eyebrow)

        title = QLabel("MusicVault")
        title.setObjectName("settingsAboutTitle")
        hero_layout.addWidget(title)

        version = QLabel("V3  •  MUSIC COLLECTION")
        version.setObjectName("settingsAboutVersion")
        hero_layout.addWidget(version)

        tagline = QLabel("Your music. Your collection. Your control.")
        tagline.setObjectName("settingsAboutTagline")
        hero_layout.addWidget(tagline)

        description = QLabel(
            "MusicVault is a personal music collection environment built to bring "
            "an entire music library together in one place — from vinyl and CDs "
            "to MP3s, livesets and everything that comes next."
        )
        description.setObjectName("settingsAboutText")
        description.setWordWrap(True)
        hero_layout.addWidget(description)
        layout.addWidget(hero)

        collection = SettingsCard(
            "Collection",
            "One home for your music",
            "Different formats, one organised collection."
        )
        collection_row = QHBoxLayout()
        collection_row.setSpacing(10)
        for name, subtitle in [
            ("VINYL", "Physical releases"),
            ("CD", "Compact disc collection"),
            ("MP3", "Digital music library"),
            ("LIVESETS", "Mixes & recordings"),
        ]:
            item = QFrame()
            item.setObjectName("settingsAboutTile")
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(14, 14, 14, 14)
            item_layout.setSpacing(3)
            item_title = QLabel(name)
            item_title.setObjectName("settingsAboutTileTitle")
            item_layout.addWidget(item_title)
            item_text = QLabel(subtitle)
            item_text.setObjectName("settingsAboutTileText")
            item_text.setWordWrap(True)
            item_layout.addWidget(item_text)
            collection_row.addWidget(item, 1)
        collection.body.addLayout(collection_row)
        layout.addWidget(collection)

        library = SettingsCard(
            "Music Library",
            "Built around the collection",
            "Tools that make a large music library easier to manage."
        )
        library.body.addWidget(SettingsRow("Automatic MP3 scanning", "Scan the digital library and keep MusicVault aware of available audio files.", QLabel("READY")))
        library.body.addWidget(SettingsRow("Track matching", "Link tracks to matching MP3 files and keep multiple versions available.", QLabel("READY")))
        library.body.addWidget(SettingsRow("Preferred versions", "Choose which linked MP3 should be used for playback when alternatives exist.", QLabel("READY")))
        library.body.addWidget(SettingsRow("Missing-file detection", "Identify broken or missing MP3 links without silently changing your collection.", QLabel("SAFE")))
        layout.addWidget(library)

        metadata = SettingsCard(
            "Discovery & Metadata",
            "More than a file browser",
            "MusicVault keeps the identity of your releases and tracks at the centre."
        )
        metadata.body.addWidget(SettingsRow("Discogs integration", "Bring release information, artwork and track metadata into your collection.", QLabel("CONNECTED")))
        metadata.body.addWidget(SettingsRow("Release organisation", "Keep artists, releases, formats and track information together.", QLabel("READY")))
        metadata.body.addWidget(SettingsRow("Artwork", "Use cover artwork to make the collection feel like a real music library.", QLabel("READY")))
        layout.addWidget(metadata)

        technology = SettingsCard(
            "Technology",
            "The engine underneath",
            "A local desktop application designed around your own collection."
        )
        technology.body.addWidget(SettingsRow("PySide6", "Modern Qt desktop interface for the MusicVault experience.", QLabel("UI")))
        technology.body.addWidget(SettingsRow("SQLite", "Local collection database for releases, tracks and library relationships.", QLabel("DATA")))
        technology.body.addWidget(SettingsRow("FFmpeg", "Audio and multimedia playback through Qt Multimedia.", QLabel("AUDIO")))
        technology.body.addWidget(SettingsRow("Discogs", "External music metadata and release enrichment.", QLabel("META")))
        layout.addWidget(technology)

        signature = QFrame()
        signature.setObjectName("settingsAboutSignature")
        signature_layout = QVBoxLayout(signature)
        signature_layout.setContentsMargins(30, 28, 30, 28)
        signature_layout.setSpacing(5)

        built = QLabel("BUILT BY KID ACID")
        built.setObjectName("settingsAboutBuilt")
        built.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signature_layout.addWidget(built)

        made = QLabel("Made for the music. Built for the collection.")
        made.setObjectName("settingsAboutMade")
        made.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signature_layout.addWidget(made)

        signature_version = QLabel("MUSICVAULT V3")
        signature_version.setObjectName("settingsAboutSignatureVersion")
        signature_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signature_layout.addWidget(signature_version)
        layout.addWidget(signature)

        scroll.setWidget(body)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)
        return page

'''

text = text[:start] + new_about + text[end:]

marker = '''            QLabel#settingsAboutTitle {\n'''
css = '''            QFrame#settingsAboutHero,\n            QFrame#settingsAboutSignature {\n                background: #111116;\n                border: 1px solid #25252f;\n                border-radius: 14px;\n            }\n\n            QLabel#settingsAboutTagline {\n                background: transparent;\n                color: #e9e9ef;\n                font-size: 17px;\n                font-weight: 750;\n                margin-top: 8px;\n            }\n\n            QFrame#settingsAboutTile {\n                background: #18181f;\n                border: 1px solid #2b2b36;\n                border-radius: 10px;\n            }\n\n            QLabel#settingsAboutTileTitle {\n                background: transparent;\n                color: #ffffff;\n                font-size: 11px;\n                font-weight: 900;\n                letter-spacing: 1px;\n            }\n\n            QLabel#settingsAboutTileText {\n                background: transparent;\n                color: #777782;\n                font-size: 10px;\n            }\n\n            QLabel#settingsAboutBuilt {\n                background: transparent;\n                color: #d84b91;\n                font-size: 18px;\n                font-weight: 950;\n                letter-spacing: 2px;\n            }\n\n            QLabel#settingsAboutMade {\n                background: transparent;\n                color: #b8b8c2;\n                font-size: 11px;\n            }\n\n            QLabel#settingsAboutSignatureVersion {\n                background: transparent;\n                color: #555560;\n                font-size: 9px;\n                font-weight: 900;\n                letter-spacing: 1.5px;\n            }\n\n'''
if marker not in text:
    raise SystemExit("CSS marker not found")
text = text.replace(marker, css + marker, 1)

path.write_text(text, encoding="utf-8")
print("MusicVault About page upgraded")
