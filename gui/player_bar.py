# ============================================================
# KID ACID'S VINYLVAULT V3
# PLAYER BAR
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
)


# ============================================================
# PLAYER BAR
# ============================================================

class PlayerBar(QWidget):

    def __init__(
        self,
        player,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.player = player

        self.build_ui()

        self.connect_player()


# ============================================================
# BUILD UI
# ============================================================

    def build_ui(self):

        self.setObjectName(
            "playerBar"
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            15,
            8,
            15,
            8
        )

        layout.setSpacing(
            8
        )

        # ----------------------------------------------------
        # TRACK INFO
        # ----------------------------------------------------

        self.track_label = QLabel(
            "Geen track"
        )

        self.track_label.setMinimumWidth(
            260
        )

        self.track_label.setMaximumWidth(
            360
        )

        self.track_label.setObjectName(
            "playerTrack"
        )

        layout.addWidget(
            self.track_label
        )

        # ----------------------------------------------------
        # PLAY
        # ----------------------------------------------------

        self.play_button = QPushButton(
            "▶"
        )

        self.play_button.setFixedSize(
            42,
            36
        )

        self.play_button.clicked.connect(
            self.toggle_play
        )

        layout.addWidget(
            self.play_button
        )

        # ----------------------------------------------------
        # STOP
        # ----------------------------------------------------

        self.stop_button = QPushButton(
            "■"
        )

        self.stop_button.setFixedSize(
            42,
            36
        )

        self.stop_button.clicked.connect(
            self.stop
        )

        layout.addWidget(
            self.stop_button
        )

        # ----------------------------------------------------
        # CURRENT TIME
        # ----------------------------------------------------

        self.position_label = QLabel(
            "00:00"
        )

        self.position_label.setFixedWidth(
            45
        )

        layout.addWidget(
            self.position_label
        )

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        self.progress_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.progress_slider.setRange(
            0,
            0
        )

        self.progress_slider.sliderMoved.connect(
            self.seek
        )

        layout.addWidget(
            self.progress_slider,
            1
        )

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        self.duration_label = QLabel(
            "00:00"
        )

        self.duration_label.setFixedWidth(
            45
        )

        layout.addWidget(
            self.duration_label
        )

        # ----------------------------------------------------
        # VOLUME
        # ----------------------------------------------------

        volume_label = QLabel(
            "VOL"
        )

        layout.addWidget(
            volume_label
        )

        self.volume_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        self.volume_slider.setRange(
            0,
            100
        )

        self.volume_slider.setValue(
            100
        )

        self.volume_slider.setFixedWidth(
            100
        )

        self.volume_slider.valueChanged.connect(
            self.change_volume
        )

        layout.addWidget(
            self.volume_slider
        )

        # ----------------------------------------------------
        # STYLE
        # ----------------------------------------------------

        self.setStyleSheet(
            """
            QWidget#playerBar {
                background-color: #181818;
                border-top: 1px solid #333333;
            }

            QLabel {
                background: transparent;
                color: #aaaaaa;
                font-size: 12px;
            }

            QLabel#playerTrack {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #333333;
            }

            QPushButton:pressed {
                background-color: #444444;
            }

            QSlider::groove:horizontal {
                background-color: #333333;
                height: 5px;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background-color: #dddddd;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            """
        )


# ============================================================
# CONNECT PLAYER
# ============================================================

    def connect_player(self):

        self.player.player.positionChanged.connect(
            self.position_changed
        )

        self.player.player.durationChanged.connect(
            self.duration_changed
        )

        self.player.player.playbackStateChanged.connect(
            self.playback_state_changed
        )

        self.player.play_started.connect(
            self.track_started
        )


# ============================================================
# PLAY FILE
# ============================================================

    def play_file(
        self,
        path
    ):

        self.player.play_file(
            path
        )


# ============================================================
# TRACK STARTED
# ============================================================

    def track_started(
        self,
        path
    ):

        filename = Path(
            path
        ).name

        self.track_label.setText(
            filename
        )


# ============================================================
# TOGGLE PLAY
# ============================================================

    def toggle_play(self):

        self.player.toggle_play()


# ============================================================
# STOP
# ============================================================

    def stop(self):

        self.player.stop()

        self.track_label.setText(
            "Geen track"
        )


# ============================================================
# SEEK
# ============================================================

    def seek(
        self,
        position
    ):

        self.player.seek(
            position
        )


# ============================================================
# VOLUME
# ============================================================

    def change_volume(
        self,
        value
    ):

        self.player.change_volume(
            value
        )


# ============================================================
# POSITION
# ============================================================

    def position_changed(
        self,
        position
    ):

        self.progress_slider.blockSignals(
            True
        )

        self.progress_slider.setValue(
            position
        )

        self.progress_slider.blockSignals(
            False
        )

        self.position_label.setText(
            self.format_time(
                position
            )
        )


# ============================================================
# DURATION
# ============================================================

    def duration_changed(
        self,
        duration
    ):

        self.progress_slider.setRange(
            0,
            duration
        )

        self.duration_label.setText(
            self.format_time(
                duration
            )
        )


# ============================================================
# PLAYBACK STATE
# ============================================================

    def playback_state_changed(
        self,
        state
    ):

        if state == (
            self.player.player.PlaybackState.PlayingState
        ):

            self.play_button.setText(
                "❚❚"
            )

        else:

            self.play_button.setText(
                "▶"
            )


# ============================================================
# FORMAT TIME
# ============================================================

    @staticmethod
    def format_time(
        milliseconds
    ):

        total_seconds = int(
            milliseconds / 1000
        )

        minutes = (
            total_seconds // 60
        )

        seconds = (
            total_seconds % 60
        )

        return (
            f"{minutes:02d}:{seconds:02d}"
        )