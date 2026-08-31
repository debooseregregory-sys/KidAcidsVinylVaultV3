# ============================================================
# KID ACID'S MUSICVAULT V3
# DISCOGS SETTINGS PANEL
# ============================================================

from gui.app_settings import paint_accent
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class DiscogsSettingsPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DiscogsSettingsPanel")
        self._settings = QSettings("Kid Acid", "MusicVault")
        self._build()
        self._style()
        self._refresh_status_labels()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        root = QVBoxLayout(body)
        root.setContentsMargins(8, 8, 12, 16)
        root.setSpacing(14)

        # ---- Hero ----
        hero = QFrame()
        hero.setObjectName("dHero")
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(20, 16, 20, 16)
        left = QVBoxLayout()
        left.setSpacing(4)
        t1 = QLabel("DISCOGS")
        t1.setObjectName("dEyebrow")
        left.addWidget(t1)
        t2 = QLabel("Connectie & import")
        t2.setObjectName("dTitle")
        left.addWidget(t2)
        t3 = QLabel(
            "Token, testverbinding en import-opties. "
            "Je collectie wordt niet aangepast tot je zelf importeert."
        )
        t3.setObjectName("dSub")
        t3.setWordWrap(True)
        left.addWidget(t3)
        hl.addLayout(left, 1)
        self.status_badge = QLabel("●  NOT CHECKED")
        self.status_badge.setObjectName("dBadge")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(self.status_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(hero)

        # ---- Connection ----
        conn = QFrame()
        conn.setObjectName("dCard")
        cl = QVBoxLayout(conn)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        cl.addWidget(self._h("CONNECTION", "Discogs token"))
        tip = QLabel(
            "Maak een token op discogs.com → Settings → Developers. "
            "Plak hieronder en klik Save token."
        )
        tip.setObjectName("dSub")
        tip.setWordWrap(True)
        cl.addWidget(tip)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.token_status = QLabel("—")
        self.token_status.setObjectName("dStatusText")
        status_row.addWidget(self.token_status, 1)
        cl.addLayout(status_row)

        token_row = QHBoxLayout()
        token_row.setSpacing(8)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("Plak hier je personal access token…")
        self.token_input.setMinimumHeight(40)
        self.token_input.setObjectName("dToken")
        token_row.addWidget(self.token_input, 1)
        save_btn = QPushButton("Save token")
        save_btn.setObjectName("dBtnPrimary")
        save_btn.setMinimumHeight(40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_token)
        token_row.addWidget(save_btn)
        cl.addLayout(token_row)

        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("dBtnPrimary")
        test_btn.setMinimumHeight(42)
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._test_connection)
        cl.addWidget(test_btn)
        root.addWidget(conn)

        # ---- Import options (checkboxes) ----
        imp = QFrame()
        imp.setObjectName("dCard")
        il = QVBoxLayout(imp)
        il.setContentsMargins(20, 16, 20, 16)
        il.setSpacing(8)
        il.addWidget(self._h("IMPORT", "Enrichment behaviour"))

        for key, label, default in [
            ("import_artwork", "Import artwork (covers meenemen)", True),
            ("enrich_metadata", "Enrich metadata (lege velden vullen)", True),
            ("preview_before_import", "Preview before import", True),
        ]:
            il.addWidget(self._check(key, label, default))
        root.addWidget(imp)

        # ---- Matching ----
        match = QFrame()
        match.setObjectName("dCard")
        ml = QVBoxLayout(match)
        ml.setContentsMargins(20, 16, 20, 16)
        ml.setSpacing(8)
        ml.addWidget(self._h("MATCHING", "Match confidence"))
        row = QHBoxLayout()
        row.setSpacing(8)
        current = str(self._settings.value("discogs_match_mode", "Balanced") or "Balanced")
        self._match_buttons = []
        for name, desc in [
            ("Strict", "Alleen hoge zekerheid"),
            ("Balanced", "Aanbevolen"),
            ("Flexible", "Meer kandidaten"),
        ]:
            b = QPushButton(f"{name}\n{desc}")
            b.setCheckable(True)
            b.setChecked(name == current)
            b.setObjectName("dChoice")
            b.setMinimumHeight(56)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda checked=False, n=name: self._set_match_mode(n))
            row.addWidget(b, 1)
            self._match_buttons.append((name, b))
        ml.addLayout(row)
        root.addWidget(match)

        # ---- Safety ----
        safe = QFrame()
        safe.setObjectName("dCard")
        sl = QVBoxLayout(safe)
        sl.setContentsMargins(20, 16, 20, 16)
        sl.setSpacing(8)
        sl.addWidget(self._h("SAFETY", "Collection safety"))
        for key, label, default in [
            ("never_overwrite_manual", "Never overwrite manual data", True),
            ("backup_before_import", "Backup before large import", True),
        ]:
            sl.addWidget(self._check(key, label, default))
        root.addWidget(safe)

        root.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _h(self, eyebrow, title):
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        e = QLabel(eyebrow)
        e.setObjectName("dEyebrow")
        v.addWidget(e)
        t = QLabel(title)
        t.setObjectName("dTitle")
        v.addWidget(t)
        return box

    def _check(self, key, label, default):
        box = QFrame()
        box.setObjectName("dCheckRow")
        lay = QHBoxLayout(box)
        lay.setContentsMargins(4, 6, 4, 6)
        cb = QCheckBox(label)
        cb.setObjectName("dCheck")
        cb.setChecked(bool(self._settings.value(key, default, type=bool)))
        cb.toggled.connect(lambda val, k=key: self._on_check(k, val))
        lay.addWidget(cb, 1)
        return box

    def _on_check(self, key, value):
        self._settings.setValue(key, bool(value))
        self.settings_changed.emit()

    def _set_match_mode(self, value):
        self._settings.setValue("discogs_match_mode", value)
        for name, button in self._match_buttons:
            button.setChecked(name == value)
        self.settings_changed.emit()

    def _refresh_status_labels(self):
        configured = self._has_configured_token()
        self.token_status.setText("CONFIGURED" if configured else "NOT CONFIGURED")
        if configured:
            self.token_input.setPlaceholderText("Token opgeslagen — plak een nieuw token om te vervangen")
        else:
            self.token_input.setPlaceholderText("Plak hier je personal access token…")

    def _has_configured_token(self):
        try:
            from gui.app_settings import paint_accent,  get_discogs_token
            return bool(get_discogs_token())
        except Exception:
            return bool(self._settings.value("discogs_token", ""))

    def _save_token(self):
        try:
            from gui.app_settings import set_discogs_token, get_discogs_token
        except Exception as exc:
            QMessageBox.critical(self, "Discogs", f"app_settings ontbreekt:\n{exc}")
            return

        typed = self.token_input.text().strip()
        if typed:
            set_discogs_token(typed)
            self.token_input.clear()
            self.status_badge.setText("●  TOKEN SAVED")
            QMessageBox.information(self, "Discogs", "Token opgeslagen.")
        else:
            if get_discogs_token():
                set_discogs_token("")
                self.status_badge.setText("●  TOKEN CLEARED")
                QMessageBox.information(self, "Discogs", "Token gewist.")
            else:
                QMessageBox.warning(self, "Discogs", "Plak eerst een token.")
        self._refresh_status_labels()
        self.settings_changed.emit()

    def _test_connection(self):
        try:
            from gui.app_settings import get_discogs_token, get_discogs_headers
            import requests
        except Exception as exc:
            QMessageBox.critical(self, "Discogs", str(exc))
            return

        if not get_discogs_token():
            self.status_badge.setText("●  NO TOKEN")
            QMessageBox.warning(
                self,
                "Discogs",
                "Geen token.\n\n"
                "1. https://www.discogs.com/settings/developers\n"
                "2. Generate new token\n"
                "3. Plak hier → Save token → Test opnieuw",
            )
            return

        self.status_badge.setText("●  TESTING…")
        try:
            response = requests.get(
                "https://api.discogs.com/oauth/identity",
                headers=get_discogs_headers(),
                timeout=20,
            )
            if response.status_code == 200:
                data = response.json()
                username = data.get("username") or data.get("name") or "ok"
                self.status_badge.setText(f"●  CONNECTED ({username})")
                self.token_status.setText("CONFIGURED")
                QMessageBox.information(self, "Discogs", f"Verbinding OK.\nIngelogd als: {username}")
            elif response.status_code in (401, 403):
                self.status_badge.setText("●  AUTH FAILED")
                QMessageBox.critical(
                    self,
                    "Discogs",
                    f"Token geweigerd (HTTP {response.status_code}).",
                )
            else:
                self.status_badge.setText(f"●  HTTP {response.status_code}")
                QMessageBox.warning(
                    self,
                    "Discogs",
                    f"HTTP {response.status_code}\n{response.text[:300]}",
                )
        except Exception as exc:
            self.status_badge.setText("●  ERROR")
            QMessageBox.critical(self, "Discogs", f"Kan Discogs niet bereiken:\n{exc}")

    def _style(self):
        # Fully self-contained — does not rely on main_window palette for readability
        self.setStyleSheet("""
            QWidget#DiscogsSettingsPanel, QScrollArea, QScrollArea > QWidget > QWidget {
                background: #0b0b0f;
                color: #f2f2f7;
            }
            QFrame#dHero, QFrame#dCard {
                background: #14141a;
                border: 1px solid #2a2a34;
                border-radius: 12px;
            }
            QLabel#dEyebrow {
                color: #d84b91;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }
            QLabel#dTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: 800;
                background: transparent;
            }
            QLabel#dSub {
                color: #c2c2ce;
                font-size: 13px;
                background: transparent;
            }
            QLabel#dStatusText {
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }
            QLabel#dBadge {
                background: #2a1524;
                color: #d84b91;
                border: 1px solid #5a2a48;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 12px;
                font-weight: 900;
                min-width: 140px;
            }
            QLineEdit#dToken {
                background: #1c1c24;
                color: #ffffff;
                border: 1px solid #3d3d4a;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
                selection-background-color: #d84b91;
            }
            QPushButton#dBtnPrimary {
                background: #d84b91;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton#dBtnPrimary:hover {
                background: #e35ba0;
            }
            QPushButton#dChoice {
                background: #1c1c24;
                color: #e8e8f0;
                border: 1px solid #3d3d4a;
                border-radius: 10px;
                padding: 10px;
                font-size: 12px;
                font-weight: 700;
                text-align: center;
            }
            QPushButton#dChoice:checked {
                background: #2a1524;
                color: #ffffff;
                border: 2px solid #d84b91;
            }
            QFrame#dCheckRow {
                background: #1a1a22;
                border: 1px solid #2e2e38;
                border-radius: 8px;
            }
            QCheckBox#dCheck {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                spacing: 10px;
                background: transparent;
                padding: 8px;
            }
            QCheckBox#dCheck::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #6a6a78;
                background: #121218;
            }
            QCheckBox#dCheck::indicator:checked {
                background: #d84b91;
                border: 2px solid #d84b91;
            }
        """)
