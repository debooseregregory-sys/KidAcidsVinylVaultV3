# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE BOARD TILE
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
)


class ReleaseBoardTile(QFrame):

    open_release = Signal(int)
    play_mp3 = Signal(str)

    def __init__(self, data, parent=None):
        super().__init__(parent)

        self.data = data
        self.setObjectName("releaseBoardTile")
        self.setMinimumWidth(250)
        self.setMaximumWidth(310)
        self.setMinimumHeight(390)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(8)

        cover = QLabel()
        cover.setObjectName("boardCover")
        cover.setFixedSize(216, 216)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.setScaledContents(False)

        cover_path = str(data.get("cover") or "").strip()
        if cover_path and Path(cover_path).exists():
            pixmap = QPixmap(cover_path)
            if not pixmap.isNull():
                cover.setPixmap(
                    pixmap.scaled(
                        216,
                        216,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            else:
                cover.setText("NO\nCOVER")
        else:
            cover.setText("NO\nCOVER")

        cover_wrap = QHBoxLayout()
        cover_wrap.addStretch()
        cover_wrap.addWidget(cover)
        cover_wrap.addStretch()
        layout.addLayout(cover_wrap)

        artist = QLabel(str(data.get("artist") or "Onbekend"))
        artist.setObjectName("boardArtist")
        artist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        artist.setWordWrap(True)
        layout.addWidget(artist)

        title = QLabel(str(data.get("title") or "(geen titel)"))
        title.setObjectName("boardTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        info_bits = []
        if data.get("label"):
            info_bits.append(str(data["label"]))
        if data.get("catalog"):
            info_bits.append(str(data["catalog"]))
        if data.get("year"):
            info_bits.append(str(data["year"]))

        info = QLabel("  •  ".join(info_bits) if info_bits else "")
        info.setObjectName("boardInfo")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)

        status = QLabel(
            "✓ KLAAR" if int(data.get("checked") or 0) == 1 else "OPEN"
        )
        status.setObjectName(
            "boardReady" if int(data.get("checked") or 0) == 1 else "boardOpen"
        )
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status)

        buttons = QHBoxLayout()
        buttons.setSpacing(7)

        open_button = QPushButton("OPEN")
        open_button.setObjectName("boardOpenButton")
        open_button.clicked.connect(
            lambda: self.open_release.emit(int(data["id"]))
        )
        buttons.addWidget(open_button)

        play_path = str(data.get("preferred_mp3") or "").strip()
        play_button = QPushButton("▶ PLAY")
        play_button.setObjectName("boardPlayButton")
        play_button.setEnabled(bool(play_path) and Path(play_path).exists())
        if play_path:
            play_button.clicked.connect(
                lambda: self.play_mp3.emit(play_path)
            )
        buttons.addWidget(play_button)

        layout.addLayout(buttons)

    def mouseDoubleClickEvent(self, event):
        self.open_release.emit(int(self.data["id"]))
        super().mouseDoubleClickEvent(event)
