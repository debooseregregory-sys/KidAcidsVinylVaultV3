# ============================================================
# KID ACID'S MUSICVAULT V3
# PLAYER SETTINGS PANEL
# ============================================================

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget


class PlayerSettingsPanel(QWidget):
    """Modern player-settings card used by the MusicVault Settings page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("Kid Acid", "MusicVault")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(2, 2, 10, 2)
        root.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("settingsHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 20, 24, 20)

        text = QVBoxLayout()
        text.setSpacing(3)
        title = QLabel("Your listening room")
        title.setObjectName("settingsHeroTitle")
        text.addWidget(title)
        description = QLabel("Shape playback without touching your collection or database.")
        description.setObjectName("settingsHeroDescription")
        description.setWordWrap(True)
        text.addWidget(description)
        hero_layout.addLayout(text, 1)

        badge = QLabel("PLAYER")
        badge.setObjectName("settingsSafeChip")
        hero_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(hero)

        card = QFrame()
        card.setObjectName("settingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(6)

        eyebrow = QLabel("PLAYBACK")
        eyebrow.setObjectName("settingsEyebrow")
        layout.addWidget(eyebrow)

        title = QLabel("Master output")
        title.setObjectName("settingsCardTitle")
        layout.addWidget(title)

        description = QLabel("Set the preferred MusicVault volume for the next session.")
        description.setObjectName("settingsCardDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        row = QHBoxLayout()
        row.setContentsMargins(0, 14, 0, 8)
        row.setSpacing(14)

        icon = QLabel("🔊")
        icon.setFixedWidth(28)
        row.addWidget(icon)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(self.settings.value("player_volume", 80, type=int))
        self.volume.valueChanged.connect(self._volume_changed)
        row.addWidget(self.volume, 1)

        self.volume_value = QLabel(f"{self.volume.value()}%")
        self.volume_value.setObjectName("settingsValueBadge")
        self.volume_value.setMinimumWidth(52)
        self.volume_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.volume_value)
        layout.addLayout(row)

        root.addWidget(card)

        options = QFrame()
        options.setObjectName("settingsCard")
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(24, 22, 24, 20)
        options_layout.setSpacing(0)

        eyebrow = QLabel("BEHAVIOUR")
        eyebrow.setObjectName("settingsEyebrow")
        options_layout.addWidget(eyebrow)

        title = QLabel("Playback flow")
        title.setObjectName("settingsCardTitle")
        options_layout.addWidget(title)

        options_layout.addWidget(self._toggle_row("Autoplay next track", "Continue automatically when a track finishes.", "autoplay", True))
        options_layout.addWidget(self._toggle_row("Visualizer", "Keep the MP3 Showcase visualizer enabled when supported.", "visualizer", True))
        options_layout.addWidget(self._toggle_row("Smooth transitions", "Reserve a short transition when moving between tracks.", "smooth_transitions", False))
        options_layout.addWidget(self._toggle_row("Remember volume", "Restore your preferred volume when MusicVault starts.", "remember_volume", True))
        root.addWidget(options)
        root.addStretch()

    def _toggle_row(self, title, description, key, default):
        row = QFrame()
        row.setObjectName("settingsRow")
        layout = QHBoxLayout(row)
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

        from gui.settings_page import SettingsToggle
        toggle = SettingsToggle(self.settings.value(key, default, type=bool))
        toggle.toggled.connect(lambda value, k=key: self.settings.setValue(k, value))
        layout.addWidget(toggle, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _volume_changed(self, value):
        self.volume_value.setText(f"{value}%")
        self.settings.setValue("player_volume", value)
