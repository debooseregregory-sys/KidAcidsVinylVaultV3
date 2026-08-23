from __future__ import annotations

from gui.app_settings import paint_accent
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class HelpCard(QFrame):
    def __init__(self, eyebrow: str, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("helpCard")
        self._search_text = f"{eyebrow} {title} {text}".casefold()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(7)

        eyebrow_label = QLabel(eyebrow.upper())
        eyebrow_label.setObjectName("helpEyebrow")
        layout.addWidget(eyebrow_label)

        title_label = QLabel(title)
        title_label.setObjectName("helpCardTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        text_label = QLabel(text)
        text_label.setObjectName("helpCardText")
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(text_label)

    def matches(self, query: str) -> bool:
        return not query or query.casefold() in self._search_text


class HelpPage(QWidget):
    """Full in-app manual for Kid Acid's MusicVault."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpPage")
        self.cards: list[HelpCard] = []
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(34, 26, 34, 24)
        outer.setSpacing(14)

        hero = QFrame()
        hero.setObjectName("helpHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 22, 28, 20)
        hero_layout.setSpacing(5)

        eyebrow = QLabel("KID ACID'S MUSICVAULT V3")
        eyebrow.setObjectName("helpHeroEyebrow")
        hero_layout.addWidget(eyebrow)

        title = QLabel("HELP & COMPLETE GUIDE")
        title.setObjectName("helpHeroTitle")
        hero_layout.addWidget(title)

        subtitle = QLabel(
            "A practical guide to your collection, playback, Discogs, Livesets and the MusicVault workflow."
        )
        subtitle.setObjectName("helpHeroSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)

        outer.addWidget(hero)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek in Help…  bv. MP3, Discogs, Livesets, cover, speler")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter_cards)
        search_row.addWidget(self.search, 1)
        clear = QPushButton("TOON ALLES")
        clear.setObjectName("helpClear")
        clear.clicked.connect(self.search.clear)
        search_row.addWidget(clear)
        outer.addLayout(search_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 10, 14)
        content_layout.setSpacing(10)

        sections = [
            ("QUICK START", "Begin hier", "Start MusicVault, open Settings if needed, check your music/MP3 location and then use the relevant Library. Open a release or liveset to inspect it and use the player to listen. The Showcase pages are for the visual presentation; Library pages are for finding and managing items."),
            ("VINYL", "Vinyl Library & Release details", "Vinyl is your main release collection. Use the Library to search and browse releases. Open a release for its cover, metadata and tracks. Linked MP3 files can be played from the track area. Keep local collection information such as your kastcode intact when editing other release data."),
            ("VINYL", "Vinyl Showcase", "Showcase is the visual way to browse and play releases. It is separate from the Library/detail editing workflow. Select a release, inspect its artwork and tracks, and use the track play controls. The active play state is shown by the player styling."),
            ("CD", "CD Library", "CD has its own Library and Showcase. Use CD Library to find a CD, then open the CD release view. CD tracks use the same central playback system as the rest of MusicVault. CD and Vinyl are kept as separate media types."),
            ("CD", "CD Showcase & tracks", "The CD Showcase is designed as the CD-specific visual presentation. Track play buttons show the active state, and playback is handled by the central player. If a track has a linked MP3, playing it should update the active track state in the Showcase."),
            ("MP3", "MP3 Library", "Use MP3 Library to search and inspect the scanned audio collection. MP3 files are the actual playable audio files; database links tell MusicVault which file belongs to a track. Do not move or rename files outside MusicVault without checking the resulting links."),
            ("MP3", "MP3 matching & links", "MusicVault can link MP3 files to tracks using matching information. A link is not the same thing as copying an MP3 into the database: the audio file remains on disk and the database stores its path/link information. If a file is missing, check the original path before trying to repair a match."),
            ("PLAYER", "The central player", "The bottom player is the common playback engine. Play a track or liveset from its page and the central player handles the actual audio. Use pause/play and other available controls there. Playback views listen to the same player state so the displayed active item stays synchronized."),
            ("LIVESETS", "Livesets Library", "Livesets have a dedicated Library for managing sets. Select a set to edit title, artist/DJ, date, location, duration, audio file and cover. Use KIES AUDIO to link the real MP3/audio file. OPSLAAN writes the metadata to data/livesets.json. The audio file itself is not copied or deleted when you save."),
            ("LIVESETS", "Liveset Showcase", "Showcase is the visual entry point for Livesets. Select a set to open its dedicated playback page. The large animated visualizer belongs to the playback/detail page, not the editing Library."),
            ("LIVESETS", "Liveset playback", "On the Liveset playback page you see the selected cover, title, artist and metadata together with PLAY LIVESET. The NOW PLAYING information is tied to the central player, so it should describe the liveset that is actually playing rather than a fixed slogan."),
            ("COVERS", "Covers toevoegen", "Use the cover controls on the relevant Library/editor page to choose an image. MusicVault stores liveset covers inside its local data/liveset_covers area. Replacing a liveset cover removes only the old managed cover file; the audio file is left alone."),
            ("DISCOGS", "Discogs import", "Discogs tools are for importing or enriching release information. Work carefully with imports and matching because Discogs data is external information while your local collection and MP3 links are your own data. Always verify the selected release before applying a large change."),
            ("DISCOGS", "Discogs matching", "When matching a release or track, compare artist, title, format, catalogue information and track listing instead of relying on one field. A good match should make sense for the physical release and your local collection. Do not use Discogs matching as a reason to overwrite unrelated local information."),
            ("SETTINGS", "Settings", "Settings contains the configuration areas used by MusicVault, including application behaviour, database options, music-library options and Discogs settings. Change one logical setting at a time and test the affected page afterwards."),
            ("DATABASE", "Database & local data", "The database contains the structured collection information and links. Local data also includes covers and liveset metadata. Database files and generated local data should not be casually deleted. If something looks wrong, stop before running cleanup or import operations."),
            ("SAFETY", "Before large changes", "For a large import, matching run or structural change, first make sure MusicVault starts correctly. Test the exact page you changed. Prefer small, understandable Git commits so a working state can be recovered easily."),
            ("SAFETY", "What not to delete", "Do not manually delete the database, cover folders or audio files just because an item is not visible in a Library. A missing file can leave a database link behind. First identify whether the problem is the database record, the path or the physical file."),
            ("TROUBLESHOOTING", "Een MP3 speelt niet", "Check whether the file still exists at the stored path. If the file was moved or renamed, the track link may point to the old location. Test the file directly and then repair the MusicVault link rather than deleting the track record."),
            ("TROUBLESHOOTING", "Een Liveset speelt niet", "Open Livesets Library, select the set and check Audio bestand. Use KIES AUDIO to select the real audio file again and click OPSLAAN. Then reopen the set from Showcase and press PLAY LIVESET."),
            ("TROUBLESHOOTING", "Een cover ontbreekt", "Open the relevant editor and choose the cover again. For Livesets, the cover is stored in the local liveset cover folder. If the image was manually removed from disk, selecting it again is the safest repair."),
            ("TROUBLESHOOTING", "MusicVault start niet", "Start run_v3.py from PowerShell and read the first Python traceback. Do not keep changing random files. A syntax error, import error or Qt error usually identifies the exact file that needs attention."),
            ("TROUBLESHOOTING", "Na een wijziging werkt iets anders niet", "Check Git status and the changed file first. Compile the affected Python file with python -m py_compile <file>. Then start MusicVault and test the affected workflow. Keep unrelated files untouched while diagnosing the problem."),
            ("GIT", "Werken met de huidige versie", "This MusicVault project is maintained on the rescue-my-work-cd branch. Before pulling new work, make sure your working tree is clean or deliberately stash/commit local changes. After a pull, compile the changed Python files and run the application."),
            ("ABOUT", "MusicVault in één zin", "Kid Acid's MusicVault is your local music collection environment: physical releases, CDs, MP3 audio and Livesets brought together with artwork, metadata, playback and visual Showcases."),
        ]

        for eyebrow, title, text in sections:
            card = HelpCard(eyebrow, title, text)
            self.cards.append(card)
            content_layout.addWidget(card)

        self.empty_label = QLabel("Geen Help-onderdeel gevonden. Probeer een ander zoekwoord.")
        self.empty_label.setObjectName("helpEmpty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        content_layout.addWidget(self.empty_label)

        footer = QLabel("KID ACID  •  MUSICVAULT V3  •  HELP")
        footer.setObjectName("helpFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(footer)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self.setStyleSheet(paint_accent("""
            QFrame#helpHero{background:#15151c;border:1px solid #30303b;border-radius:14px;}
            QLabel#helpHeroEyebrow{color:#ffcf72;font-size:10px;font-weight:900;letter-spacing:2px;}
            QLabel#helpHeroTitle{color:#fff;font-size:29px;font-weight:900;}
            QLabel#helpHeroSubtitle{color:#a6a6b0;font-size:13px;}
            QLineEdit{background:#0e0e12;color:#fff;border:1px solid #30303a;border-radius:8px;padding:10px 12px;font-size:12px;}
            QLineEdit:focus{border-color:#ffcf72;}
            QPushButton#helpClear{background:#18181f;color:#ddd;border:1px solid #30303a;border-radius:8px;padding:10px 15px;font-size:10px;font-weight:900;}
            QPushButton#helpClear:hover{background:#24242c;color:#fff;border-color:#ffcf72;}
            QFrame#helpCard{background:#111116;border:1px solid #292933;border-radius:11px;}
            QFrame#helpCard:hover{border-color:#4a4a58;background:#13131a;}
            QLabel#helpEyebrow{color:#ffcf72;font-size:9px;font-weight:900;letter-spacing:1.5px;}
            QLabel#helpCardTitle{color:#fff;font-size:17px;font-weight:900;}
            QLabel#helpCardText{color:#aaaab4;font-size:12px;}
            QLabel#helpEmpty{color:#ffcf72;font-size:13px;font-weight:800;padding:30px;}
            QLabel#helpFooter{color:#686872;font-size:10px;font-weight:800;padding:10px;}
            QScrollBar:vertical{background:#0d0d11;width:10px;border-radius:5px;}
            QScrollBar::handle:vertical{background:#34343e;border-radius:5px;min-height:35px;}
            QScrollBar::handle:vertical:hover{background:#50505c;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
        """))

    def _filter_cards(self, text: str):
        query = text.strip()
        visible = 0
        for card in self.cards:
            show = card.matches(query)
            card.setVisible(show)
            if show:
                visible += 1
        self.empty_label.setVisible(visible == 0)
