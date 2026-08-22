# ============================================================
# KID ACID'S MUSICVAULT V3
# DISCOGS SETTINGS PANEL
# ============================================================

from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DiscogsSettingsPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("Kid Acid", "MusicVault")
        self._build()
        self._style()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(2, 2, 10, 8)
        root.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("discogsHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 20, 24, 20)

        text = QVBoxLayout()
        text.setSpacing(4)
        eyebrow = QLabel("DISCOGS")
        eyebrow.setObjectName("discogsEyebrow")
        text.addWidget(eyebrow)
        title = QLabel("Connect your music world")
        title.setObjectName("discogsHeroTitle")
        text.addWidget(title)
        description = QLabel(
            "Control Discogs connection, enrichment and import behaviour without changing your existing collection."
        )
        description.setObjectName("discogsHeroDescription")
        description.setWordWrap(True)
        text.addWidget(description)
        hero_layout.addLayout(text, 1)

        self.status_badge = QLabel("●  NOT CHECKED")
        self.status_badge.setObjectName("discogsStatusBadge")
        hero_layout.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(hero)

        connection = self._card(
            "CONNECTION",
            "Discogs connection",
            "Your existing Discogs authentication remains untouched."
        )
        connection.body.addWidget(self._row(
            "API credentials",
            "Credentials are never displayed here in plain text.",
            self._value("CONFIGURED" if self._has_configured_token() else "NOT CONFIGURED")
        ))

        test = QPushButton("Test Connection  →")
        test.setObjectName("discogsAction")
        test.setCursor(Qt.CursorShape.PointingHandCursor)
        test.clicked.connect(self._test_connection)
        connection.body.addWidget(test)
        root.addWidget(connection)

        import_card = self._card(
            "IMPORT",
            "Enrichment behaviour",
            "Choose how much metadata MusicVault should request when importing releases."
        )
        import_card.body.addWidget(self._toggle_row(
            "Import artwork",
            "Allow artwork to be included when Discogs data is imported.",
            "import_artwork",
            True,
        ))
        import_card.body.addWidget(self._toggle_row(
            "Enrich metadata",
            "Use Discogs information to fill missing release metadata.",
            "enrich_metadata",
            True,
        ))
        import_card.body.addWidget(self._toggle_row(
            "Preview before import",
            "Show a review step before a Discogs import changes the collection.",
            "preview_before_import",
            True,
        ))
        root.addWidget(import_card)

        matching = self._card(
            "MATCHING",
            "Match confidence",
            "Keep automatic matching conservative so your manually curated collection stays safe."
        )
        choices = QHBoxLayout()
        choices.setSpacing(10)
        current = self._settings.value("discogs_match_mode", "Balanced")
        for name, description in [
            ("Strict", "High confidence"),
            ("Balanced", "Recommended"),
            ("Flexible", "More candidates"),
        ]:
            button = QPushButton(f"{name}\n{description}")
            button.setCheckable(True)
            button.setChecked(name == current)
            button.setObjectName("discogsChoice")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, value=name: self._set_match_mode(value))
            choices.addWidget(button, 1)
        matching.body.addLayout(choices)
        root.addWidget(matching)

        safety = self._card(
            "SAFETY",
            "Protect manual work",
            "These preferences are local MusicVault settings. They do not alter existing database records by themselves."
        )
        safety.body.addWidget(self._toggle_row(
            "Never overwrite manual data",
            "Prefer your curated values when Discogs has different metadata.",
            "never_overwrite_manual",
            True,
        ))
        safety.body.addWidget(self._toggle_row(
            "Backup before large import",
            "Keep a safety copy before a future bulk-import operation.",
            "backup_before_import",
            True,
        ))
        root.addWidget(safety)
        root.addStretch()

    def _card(self, eyebrow, title, description):
        card = QFrame()
        card.setObjectName("discogsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(5)

        small = QLabel(eyebrow)
        small.setObjectName("discogsSmall")
        layout.addWidget(small)
        heading = QLabel(title)
        heading.setObjectName("discogsCardTitle")
        layout.addWidget(heading)
        desc = QLabel(description)
        desc.setObjectName("discogsCardDescription")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        body = QVBoxLayout()
        body.setContentsMargins(0, 10, 0, 0)
        body.setSpacing(8)
        layout.addLayout(body)
        card.body = body
        return card

    def _row(self, title, description, control):
        row = QFrame()
        row.setObjectName("discogsRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 10, 0, 10)
        text = QVBoxLayout()
        text.setSpacing(2)
        name = QLabel(title)
        name.setObjectName("discogsRowTitle")
        text.addWidget(name)
        desc = QLabel(description)
        desc.setObjectName("discogsRowDescription")
        desc.setWordWrap(True)
        text.addWidget(desc)
        layout.addLayout(text, 1)
        layout.addWidget(control)
        return row

    def _toggle_row(self, title, description, key, default):
        button = QPushButton("ON" if self._settings.value(key, default, type=bool) else "OFF")
        button.setCheckable(True)
        button.setChecked(self._settings.value(key, default, type=bool))
        button.setObjectName("discogsToggle")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False, b=button, k=key: self._toggle(b, k))
        return self._row(title, description, button)

    def _value(self, text):
        label = QLabel(text)
        label.setObjectName("discogsValue")
        return label

    def _toggle(self, button, key):
        self._settings.setValue(key, button.isChecked())
        button.setText("ON" if button.isChecked() else "OFF")
        self.settings_changed.emit()

    def _set_match_mode(self, value):
        self._settings.setValue("discogs_match_mode", value)
        self.settings_changed.emit()

    def _has_configured_token(self):
        # Deliberately inspect only safe presence indicators; never expose a token.
        keys = ("discogs_token", "DISCOGS_TOKEN", "token")
        return any(bool(self._settings.value(key, "")) for key in keys)

    def _test_connection(self):
        # Safe UI test for now. Existing Discogs code is intentionally untouched.
        self.status_badge.setText("●  READY TO TEST")
        self.status_badge.setProperty("state", "ready")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def _style(self):
        self.setStyleSheet("""
            QFrame#discogsHero, QFrame#discogsCard {
                background: #111116;
                border: 1px solid #25252f;
                border-radius: 14px;
            }
            QLabel#discogsEyebrow, QLabel#discogsSmall {
                background: transparent;
                color: #d84b91;
                font-size: 9px;
                font-weight: 900;
                letter-spacing: 1.7px;
            }
            QLabel#discogsHeroTitle {
                background: transparent;
                color: #ffffff;
                font-size: 25px;
                font-weight: 800;
            }
            QLabel#discogsHeroDescription, QLabel#discogsCardDescription, QLabel#discogsRowDescription {
                background: transparent;
                color: #777782;
                font-size: 11px;
            }
            QLabel#discogsStatusBadge {
                background: #1b171d;
                color: #d84b91;
                border: 1px solid #4a293c;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 9px;
                font-weight: 900;
            }
            QLabel#discogsCardTitle {
                background: transparent;
                color: #f4f4f7;
                font-size: 18px;
                font-weight: 800;
            }
            QFrame#discogsRow {
                background: transparent;
                border-bottom: 1px solid #25252f;
            }
            QLabel#discogsRowTitle {
                background: transparent;
                color: #eeeeF2;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#discogsValue {
                background: #19191f;
                color: #a8a8b2;
                border: 1px solid #30303a;
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 9px;
                font-weight: 800;
            }
            QPushButton#discogsAction {
                background: #d84b91;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 11px 16px;
                font-size: 11px;
                font-weight: 800;
            }
            QPushButton#discogsAction:hover { background: #e35ba0; }
            QPushButton#discogsToggle, QPushButton#discogsChoice {
                background: #18181f;
                color: #a8a8b2;
                border: 1px solid #30303a;
                border-radius: 9px;
                padding: 8px 12px;
                font-size: 9px;
                font-weight: 800;
            }
            QPushButton#discogsToggle:checked, QPushButton#discogsChoice:checked {
                background: #241722;
                color: #f0d4e2;
                border: 1px solid #d84b91;
            }
            QPushButton#discogsChoice { min-height: 48px; text-align: left; }
        """)
