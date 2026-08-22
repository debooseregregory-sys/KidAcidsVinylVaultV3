# ============================================================
# KID ACID'S MUSICVAULT V3
# SETTINGS PAGE
# ============================================================

from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsToggle(QPushButton):
    """Small, visual on/off switch used by the settings cards."""

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("settingsToggle")


class SettingsRow(QFrame):
    def __init__(self, title, description, control, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 14)
        layout.setSpacing(20)

        text = QVBoxLayout()
        text.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName("settingsRowTitle")
        text.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setObjectName("settingsRowDescription")
        description_label.setWordWrap(True)
        text.addWidget(description_label)

        layout.addLayout(text, 1)
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)


class SettingsCard(QFrame):
    def __init__(self, eyebrow, title, description, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(5)

        eyebrow_label = QLabel(eyebrow.upper())
        eyebrow_label.setObjectName("settingsEyebrow")
        layout.addWidget(eyebrow_label)

        title_label = QLabel(title)
        title_label.setObjectName("settingsCardTitle")
        layout.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setObjectName("settingsCardDescription")
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 10, 0, 0)
        self.body.setSpacing(0)
        layout.addLayout(self.body)


class AppearanceOption(QPushButton):
    def __init__(self, title, subtitle, value, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("appearanceOption")
        self.setMinimumHeight(64)
        self._title = title
        self._subtitle = subtitle
        self._value = value
        self.setText(f"{title}\n{subtitle}")


class SettingsPage(QWidget):
    page_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self._settings = QSettings("Kid Acid", "MusicVault")
        self._build()
        self._apply_style()

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(34, 30, 34, 30)
        outer.setSpacing(24)

        navigation = QFrame()
        navigation.setObjectName("settingsNavigation")
        navigation.setFixedWidth(220)

        nav_layout = QVBoxLayout(navigation)
        nav_layout.setContentsMargins(18, 20, 18, 18)
        nav_layout.setSpacing(6)

        overline = QLabel("MUSICVAULT")
        overline.setObjectName("settingsNavOverline")
        nav_layout.addWidget(overline)

        heading = QLabel("SETTINGS")
        heading.setObjectName("settingsNavHeading")
        nav_layout.addWidget(heading)

        intro = QLabel("Make MusicVault feel exactly the way you want it.")
        intro.setObjectName("settingsNavIntro")
        intro.setWordWrap(True)
        nav_layout.addWidget(intro)
        nav_layout.addSpacing(18)

        self.nav_buttons = []
        categories = [
            ("✦", "General"),
            ("◌", "Appearance"),
            ("▶", "Player"),
            ("♫", "Music Library"),
            ("◈", "Discogs"),
            ("▣", "Database"),
            ("ⓘ", "About"),
        ]

        for icon, text in categories:
            button = QPushButton()
            button.setObjectName("settingsNavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(44)

            row = QHBoxLayout(button)
            row.setContentsMargins(12, 0, 12, 0)
            row.setSpacing(12)

            icon_label = QLabel(icon)
            icon_label.setObjectName("settingsNavIcon")
            icon_label.setFixedWidth(22)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(icon_label)

            text_label = QLabel(text)
            text_label.setObjectName("settingsNavText")
            row.addWidget(text_label)
            row.addStretch()

            button.clicked.connect(lambda checked=False, name=text: self._select_category(name))
            nav_layout.addWidget(button)
            self.nav_buttons.append((text, button))

        nav_layout.addStretch()

        footer = QLabel("KID ACID  •  MUSIC COLLECTION")
        footer.setObjectName("settingsNavFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(footer)

        outer.addWidget(navigation)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        header = QFrame()
        header.setObjectName("settingsHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)

        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("Settings")
        title.setObjectName("settingsPageTitle")
        header_text.addWidget(title)

        subtitle = QLabel("A clean control room for your MusicVault experience.")
        subtitle.setObjectName("settingsPageSubtitle")
        header_text.addWidget(subtitle)

        header_layout.addLayout(header_text)
        header_layout.addStretch()

        status = QLabel("●  READY")
        status.setObjectName("settingsReadyBadge")
        header_layout.addWidget(status, 0, Qt.AlignmentFlag.AlignVCenter)

        content_layout.addWidget(header)

        self.stack = QStackedWidget()
        self.stack.setObjectName("settingsStack")
        content_layout.addWidget(self.stack, 1)

        self.stack.addWidget(self._general_page())
        self.stack.addWidget(self._appearance_page())
        self.stack.addWidget(self._placeholder_page("Player", "Playback behaviour, volume, transitions and visualizer preferences will live here."))
        self.stack.addWidget(self._placeholder_page("Music Library", "MP3 scanning, matching behaviour and library presentation will live here."))
        self.stack.addWidget(self._placeholder_page("Discogs", "Discogs connection and enrichment preferences will live here."))
        self.stack.addWidget(self._placeholder_page("Database", "Safe database information and backup tools will live here."))
        self.stack.addWidget(self._about_page())

        outer.addWidget(content, 1)
        self._select_category("General")

    def _general_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 10, 2)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("settingsHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 20, 24, 20)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(3)
        hero_title = QLabel("Your workspace")
        hero_title.setObjectName("settingsHeroTitle")
        hero_text.addWidget(hero_title)
        hero_description = QLabel("Start with the essentials. Every setting is designed to stay out of your collection until you explicitly change it.")
        hero_description.setObjectName("settingsHeroDescription")
        hero_description.setWordWrap(True)
        hero_text.addWidget(hero_description)
        hero_layout.addLayout(hero_text, 1)

        chip = QLabel("SAFE BY DEFAULT")
        chip.setObjectName("settingsSafeChip")
        hero_layout.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(hero)

        startup = SettingsCard("Startup", "Launch behaviour", "Choose how MusicVault should feel when you open it.")
        startup.body.addWidget(SettingsRow("Start page", "The page MusicVault opens first.", self._value_button("Dashboard")))
        startup.body.addWidget(SettingsRow("Remember last page", "Return to the page you were using when you closed MusicVault.", SettingsToggle(True)))
        layout.addWidget(startup)

        behaviour = SettingsCard("Behaviour", "Small details, your way", "Keep the interface predictable and comfortable during everyday use.")
        behaviour.body.addWidget(SettingsRow("Remember window state", "Keep your window size and position between sessions.", SettingsToggle(True)))
        behaviour.body.addWidget(SettingsRow("Show notifications", "Display lightweight feedback for completed actions.", SettingsToggle(True)))
        behaviour.body.addWidget(SettingsRow("Confirm before deleting", "Ask before a destructive action is performed.", SettingsToggle(True)))
        layout.addWidget(behaviour)

        layout.addStretch()
        return page

    def _appearance_page(self):
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
        hero.setObjectName("settingsHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 20, 24, 20)
        text = QVBoxLayout()
        title = QLabel("Make it yours")
        title.setObjectName("settingsHeroTitle")
        text.addWidget(title)
        desc = QLabel("Choose the visual language that follows you through MusicVault.")
        desc.setObjectName("settingsHeroDescription")
        desc.setWordWrap(True)
        text.addWidget(desc)
        hero_layout.addLayout(text, 1)
        chip = QLabel("SAVED LOCALLY")
        chip.setObjectName("settingsSafeChip")
        hero_layout.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(hero)

        accent = SettingsCard("Accent", "Signature colour", "Your accent preference is stored locally and can be changed at any time.")
        self.accent_buttons = []
        accents = [
            ("Rose", "MusicVault pink", "#d84b91"),
            ("Crimson", "Deep red", "#c73b4f"),
            ("Electric", "Bright violet", "#8f63ff"),
            ("Ice", "Cool cyan", "#55c9d8"),
        ]
        row = QHBoxLayout()
        row.setSpacing(10)
        current = self._settings.value("accent", "Rose")
        for name, subtitle, color in accents:
            button = AppearanceOption(name, subtitle, name)
            button.setStyleSheet(
                f"QPushButton#appearanceOption {{ border:1px solid #30303a; border-radius:10px; background:#18181f; color:#f0f0f4; padding:10px; text-align:left; }}"
                f"QPushButton#appearanceOption:checked {{ border:2px solid {color}; background:#21151d; }}"
            )
            button.clicked.connect(lambda checked=False, n=name: self._set_accent(n))
            button.setChecked(name == current)
            row.addWidget(button, 1)
            self.accent_buttons.append((name, button))
        accent.body.addLayout(row)
        layout.addWidget(accent)

        density = SettingsCard("Interface", "Collection density", "Choose how much breathing room you want around track and library rows.")
        self.density_buttons = []
        density_row = QHBoxLayout()
        density_row.setSpacing(10)
        current_density = self._settings.value("density", "Comfortable")
        for name, subtitle in [("Comfortable", "Balanced spacing"), ("Compact", "More tracks on screen")]:
            button = AppearanceOption(name, subtitle, name)
            button.clicked.connect(lambda checked=False, n=name: self._set_density(n))
            button.setChecked(name == current_density)
            density_row.addWidget(button, 1)
            self.density_buttons.append((name, button))
        density.body.addLayout(density_row)
        layout.addWidget(density)

        artwork = SettingsCard("Artwork", "Cover presentation", "Control how prominent cover artwork should feel throughout the collection.")
        artwork.body.addWidget(SettingsRow("Show artwork animations", "Keep subtle artwork motion enabled where supported.", SettingsToggle(self._settings.value("artwork_animations", True, type=bool))))
        artwork.body.addWidget(SettingsRow("Prefer large covers", "Give cover art more visual weight in collection views.", SettingsToggle(self._settings.value("large_covers", True, type=bool))))
        layout.addWidget(artwork)
        layout.addStretch()

        scroll.setWidget(body)
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)
        return page

    def _set_accent(self, name):
        self._settings.setValue("accent", name)
        for current, button in self.accent_buttons:
            button.setChecked(current == name)

    def _set_density(self, name):
        self._settings.setValue("density", name)
        for current, button in self.density_buttons:
            button.setChecked(current == name)

    def _placeholder_page(self, title, description):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 10, 2)

        card = QFrame()
        card.setObjectName("settingsComingSoon")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(8)

        eyebrow = QLabel("MUSICVAULT SETTINGS")
        eyebrow.setObjectName("settingsEyebrow")
        card_layout.addWidget(eyebrow)

        title_label = QLabel(title)
        title_label.setObjectName("settingsComingSoonTitle")
        card_layout.addWidget(title_label)

        description_label = QLabel(description)
        description_label.setObjectName("settingsComingSoonText")
        description_label.setWordWrap(True)
        card_layout.addWidget(description_label)

        badge = QLabel("DESIGN READY  •  FUNCTIONALITY NEXT")
        badge.setObjectName("settingsComingSoonBadge")
        card_layout.addWidget(badge)
        card_layout.addStretch()

        layout.addWidget(card, 1)
        return page

    def _about_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(2, 2, 10, 2)

        card = QFrame()
        card.setObjectName("settingsAboutCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(7)

        small = QLabel("KID ACID'S")
        small.setObjectName("settingsAboutSmall")
        card_layout.addWidget(small)

        title = QLabel("MusicVault")
        title.setObjectName("settingsAboutTitle")
        card_layout.addWidget(title)

        version = QLabel("V3  •  MUSIC COLLECTION")
        version.setObjectName("settingsAboutVersion")
        card_layout.addWidget(version)

        description = QLabel("Your personal music collection environment — vinyl, CD, MP3, livesets and everything that comes next.")
        description.setObjectName("settingsAboutText")
        description.setWordWrap(True)
        card_layout.addSpacing(10)
        card_layout.addWidget(description)

        card_layout.addStretch()
        layout.addWidget(card, 1)
        return page

    def _value_button(self, value):
        button = QPushButton(f"{value}  ▾")
        button.setObjectName("settingsValueButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(150)
        button.setMinimumHeight(38)
        return button

    def _select_category(self, name):
        for index, (text, button) in enumerate(self.nav_buttons):
            active = text == name
            button.setChecked(active)
            if active:
                self.stack.setCurrentIndex(index)

        self.page_changed.emit(name)

    def _apply_style(self):
        self.setStyleSheet(
            """
            QWidget#settingsPage {
                background: #0b0b0f;
                color: #f4f4f7;
            }

            QFrame#settingsNavigation,
            QFrame#settingsHeader,
            QFrame#settingsHero,
            QFrame#settingsCard,
            QFrame#settingsComingSoon,
            QFrame#settingsAboutCard {
                background: #111116;
                border: 1px solid #25252f;
                border-radius: 14px;
            }

            QFrame#settingsNavigation {
                background: #101015;
            }

            QLabel#settingsNavOverline,
            QLabel#settingsEyebrow,
            QLabel#settingsAboutSmall {
                background: transparent;
                color: #d84b91;
                font-size: 9px;
                font-weight: 900;
                letter-spacing: 1.8px;
            }

            QLabel#settingsNavHeading {
                background: transparent;
                color: #ffffff;
                font-size: 25px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#settingsNavIntro,
            QLabel#settingsNavFooter,
            QLabel#settingsPageSubtitle,
            QLabel#settingsCardDescription,
            QLabel#settingsHeroDescription,
            QLabel#settingsComingSoonText,
            QLabel#settingsAboutText,
            QLabel#settingsRowDescription {
                background: transparent;
                color: #777782;
                font-size: 11px;
            }

            QLabel#settingsNavFooter {
                color: #4d4d57;
                font-size: 8px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QPushButton#settingsNavButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 9px;
                color: #c9c9d1;
                text-align: left;
            }

            QPushButton#settingsNavButton:hover {
                background: #1b1820;
                border: 1px solid #2d2731;
            }

            QPushButton#settingsNavButton:checked {
                background: #281522;
                border: 1px solid #5d2947;
                color: #ffffff;
            }

            QLabel#settingsNavIcon {
                background: transparent;
                color: #777782;
                font-size: 15px;
                font-weight: 800;
            }

            QPushButton#settingsNavButton:checked QLabel#settingsNavIcon {
                color: #e05299;
            }

            QLabel#settingsNavText {
                background: transparent;
                color: #d7d7de;
                font-size: 12px;
                font-weight: 650;
            }

            QPushButton#settingsNavButton:checked QLabel#settingsNavText {
                color: #ffffff;
            }

            QLabel#settingsPageTitle {
                background: transparent;
                color: #ffffff;
                font-size: 24px;
                font-weight: 800;
            }

            QLabel#settingsReadyBadge,
            QLabel#settingsSafeChip,
            QLabel#settingsComingSoonBadge {
                background: #19131a;
                color: #d84b91;
                border: 1px solid #492b3d;
                border-radius: 12px;
                padding: 6px 10px;
                font-size: 9px;
                font-weight: 900;
                letter-spacing: 1px;
            }

            QLabel#settingsHeroTitle,
            QLabel#settingsCardTitle,
            QLabel#settingsComingSoonTitle {
                background: transparent;
                color: #ffffff;
                font-size: 17px;
                font-weight: 750;
            }

            QLabel#settingsHeroTitle {
                font-size: 18px;
            }

            QLabel#settingsRowTitle {
                background: transparent;
                color: #ededf2;
                font-size: 12px;
                font-weight: 700;
            }

            QFrame#settingsRow {
                background: transparent;
                border-bottom: 1px solid #24242d;
            }

            QFrame#settingsRow:last-child {
                border-bottom: none;
            }

            QPushButton#settingsToggle {
                background: #27272f;
                border: 1px solid #393943;
                border-radius: 13px;
                padding: 0;
            }

            QPushButton#settingsToggle:checked {
                background: #7d3157;
                border: 1px solid #a74374;
            }

            QPushButton#settingsValueButton {
                background: #18181f;
                color: #ededf2;
                border: 1px solid #30303a;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 650;
            }

            QPushButton#settingsValueButton:hover {
                border: 1px solid #d84b91;
                background: #201720;
            }

            QPushButton#appearanceOption {
                background: #18181f;
                color: #ededf2;
                border: 1px solid #30303a;
                border-radius: 10px;
                padding: 10px;
                text-align: left;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton#appearanceOption:hover {
                border: 1px solid #6c3b57;
                background: #201720;
            }

            QPushButton#appearanceOption:checked {
                border: 2px solid #d84b91;
                background: #251720;
            }

            QLabel#settingsComingSoonBadge {
                margin-top: 12px;
            }

            QLabel#settingsAboutTitle {
                background: transparent;
                color: #ffffff;
                font-size: 34px;
                font-weight: 850;
            }

            QLabel#settingsAboutVersion {
                background: transparent;
                color: #d84b91;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1.5px;
            }
            """
        )
