from __future__ import annotations

from gui.app_settings import paint_accent
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class HelpCard(QFrame):
    def __init__(self, eyebrow: str, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("helpCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(7)

        eyebrow_label = QLabel(eyebrow.upper())
        eyebrow_label.setObjectName("helpEyebrow")
        layout.addWidget(eyebrow_label)

        title_label = QLabel(title)
        title_label.setObjectName("helpCardTitle")
        layout.addWidget(title_label)

        text_label = QLabel(text)
        text_label.setObjectName("helpCardText")
        text_label.setWordWrap(True)
        layout.addWidget(text_label)


class HelpPage(QWidget):
    """Built-in Help / quick guide for Kid Acid's MusicVault."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpPage")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(34, 28, 34, 26)
        outer.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("helpHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(5)

        eyebrow = QLabel("KID ACID'S MUSICVAULT V3")
        eyebrow.setObjectName("helpHeroEyebrow")
        hero_layout.addWidget(eyebrow)

        title = QLabel("HELP & QUICK GUIDE")
        title.setObjectName("helpHeroTitle")
        hero_layout.addWidget(title)

        subtitle = QLabel(
            "Everything you need to find, play, manage and enjoy your music collection."
        )
        subtitle.setObjectName("helpHeroSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)

        outer.addWidget(hero)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 10, 12)
        content_layout.setSpacing(12)

        cards = [
            (
                "VINYL",
                "Showcase & Release Library",
                "Use Showcase for the visual presentation of a release. Release Library is the main collection view. Select a release to open its details, inspect tracks and play linked MP3 files.",
            ),
            (
                "MP3",
                "Library & Showcase",
                "MP3 Library is for searching and managing your audio collection. MP3 Showcase is the visual player area. The player bar at the bottom remains available while you browse.",
            ),
            (
                "CD",
                "CD Library",
                "The CD section is kept separate from Vinyl. Use CD Library to browse the CD collection and open its details. CD playback uses the same MusicVault player system.",
            ),
            (
                "LIVESETS",
                "Library & Playback",
                "Livesets are managed in their own library. Open a set to see its cover, artist, title and metadata, then use PLAY LIVESET. The playback page contains the animated visualizer for the active set.",
            ),
            (
                "DISCOGS",
                "Import & Enrichment",
                "Discogs tools are used to enrich the collection with release information. Keep your local collection and MP3 links intact when working with imports or matching.",
            ),
            (
                "PLAYER",
                "Playing music",
                "The player bar is the central playback control. When audio is playing, the active track or liveset is reflected in the relevant playback view. Use the player controls to pause, resume and move through audio where supported.",
            ),
            (
                "SETTINGS",
                "Make MusicVault yours",
                "Settings contains general options, appearance, player behaviour, music-library settings, Discogs settings, database tools and application information.",
            ),
            (
                "TIP",
                "A safe way to work",
                "If you make a larger change, first make sure the application starts and the relevant page still opens. Keep the Git branch clean and commit working changes in small, understandable steps.",
            ),
        ]

        for eyebrow, title, text in cards:
            content_layout.addWidget(HelpCard(eyebrow, title, text))

        footer = QLabel("KID ACID  •  MUSIC COLLECTION  •  V3")
        footer.setObjectName("helpFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(footer)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self.setStyleSheet(paint_accent("""
            QFrame#helpHero{background:#15151c;border:1px solid #30303b;border-radius:14px;}
            QLabel#helpHeroEyebrow{color:#ffcf72;font-size:10px;font-weight:900;letter-spacing:2px;}
            QLabel#helpHeroTitle{color:#fff;font-size:30px;font-weight:900;}
            QLabel#helpHeroSubtitle{color:#a6a6b0;font-size:13px;}
            QFrame#helpCard{background:#111116;border:1px solid #292933;border-radius:11px;}
            QFrame#helpCard:hover{border-color:#4a4a58;}
            QLabel#helpEyebrow{color:#ffcf72;font-size:9px;font-weight:900;letter-spacing:1.5px;}
            QLabel#helpCardTitle{color:#fff;font-size:17px;font-weight:900;}
            QLabel#helpCardText{color:#aaaab4;font-size:12px;line-height:1.45;}
            QLabel#helpFooter{color:#686872;font-size:10px;font-weight:800;padding:8px;}
            QScrollBar:vertical{background:#0d0d11;width:10px;border-radius:5px;}
            QScrollBar::handle:vertical{background:#34343e;border-radius:5px;min-height:35px;}
            QScrollBar::handle:vertical:hover{background:#50505c;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
        """))
