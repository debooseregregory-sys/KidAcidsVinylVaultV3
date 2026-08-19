# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 PLAYER
# ============================================================

from pathlib import Path

from PySide6.QtCore import Signal, QUrl
from PySide6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput,
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
)


# ============================================================
# MP3 PLAYER
# ============================================================

class MP3Player(QWidget):

    play_started = Signal(str)
    stopped = Signal()

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.current_path = None

        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)

        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        self.player.positionChanged.connect(
            self.position_changed
        )

        self.player.durationChanged.connect(
            self.duration_changed
        )

        self.player.playbackStateChanged.connect(
            self.playback_state_changed
        )

        self.player.errorOccurred.connect(
            self._player_error
        )

        self.player.mediaStatusChanged.connect(
            self._media_status
        )

        self.build_ui()


# ============================================================
# PLAYER DIAGNOSTICS
# ============================================================

    def _player_error(self, error, error_string):

        print("========================================")
        print("MP3 PLAYER ERROR")
        print("ERROR:", error)
        print("MESSAGE:", error_string)
        print("SOURCE:", self.player.source().toString())
        print("========================================")

        self.track_label.setText(
            "MP3 ERROR: " + str(error_string or error)
        )

    def _media_status(self, status):
        print("MP3 MEDIA STATUS:", status)


# ============================================================
# BUILD UI
# ============================================================

    def build_ui(self):

        self.setObjectName(
            "mp3Player"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            12,
            10,
            12,
            10
        )

        layout.setSpacing(
            6
        )

        self.track_label = QLabel(
            "Geen track geladen"
        )

        self.track_label.setObjectName(
            "playerTrack"
        )

        layout.addWidget(
            self.track_label
        )

        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.play_button = QPushButton("▶ PLAY")
        self.play_button.setMinimumWidth(90)
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)

        self.stop_button = QPushButton("■ STOP")
        self.stop_button.setMinimumWidth(90)
        self.stop_button.clicked.connect(self.stop)
        controls.addWidget(self.stop_button)

        self.position_label = QLabel("00:00")
        controls.addWidget(self.position_label)

        self.slider = QSlider()
        self.slider.setOrientation(
            __import__(
                "PySide6.QtCore",
                fromlist=["Qt"]
            ).Qt.Orientation.Horizontal
        )
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.seek)
        controls.addWidget(self.slider, 1)

        self.duration_label = QLabel("00:00")
        controls.addWidget(self.duration_label)

        layout.addLayout(controls)

        volume_layout = QHBoxLayout()

        volume_label = QLabel("Volume")
        volume_layout.addWidget(volume_label)

        self.volume_slider = QSlider()
        self.volume_slider.setOrientation(
            __import__(
                "PySide6.QtCore",
                fromlist=["Qt"]
            ).Qt.Orientation.Horizontal
        )
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        layout.addLayout(volume_layout)

        self.setStyleSheet(
            """
            QWidget#mp3Player {
                background-color: #181818;
                border-top: 1px solid #333333;
            }
            QLabel {
                background: transparent;
                color: #cccccc;
            }
            QLabel#playerTrack {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QSlider::groove:horizontal {
                background: #333333;
                height: 5px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #dddddd;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            """
        )


# ============================================================
# PLAY FILE
# ============================================================

    def play_file(
        self,
        path
    ):

        if not path:
            return

        file_path = Path(path).expanduser().resolve()

        if not file_path.exists():
            self.track_label.setText(
                "MP3 niet gevonden: " + str(file_path)
            )
            print("MP3 NIET GEVONDEN:", file_path)
            return

        if not file_path.is_file():
            self.track_label.setText(
                "Geen geldig MP3-bestand: " + str(file_path)
            )
            print("GEEN BESTAND:", file_path)
            return

        self.current_path = str(file_path)
        self.track_label.setText(file_path.name)

        print("MP3 PLAY:", self.current_path)

        self.player.stop()
        self.player.setPosition(0)

        url = QUrl.fromLocalFile(self.current_path)
        print("MP3 URL:", url.toString())

        self.player.setSource(url)
        self.player.play()

        self.play_started.emit(self.current_path)


# ============================================================
# TOGGLE PLAY
# ============================================================

    def toggle_play(self):

        if self.player.playbackState() == (
            QMediaPlayer.PlaybackState.PlayingState
        ):
            self.player.pause()
        elif self.current_path:
            self.player.play()


# ============================================================
# STOP
# ============================================================

    def stop(self):

        self.player.stop()
        self.slider.setValue(0)
        self.position_label.setText("00:00")
        self.stopped.emit()


# ============================================================
# SEEK
# ============================================================

    def seek(
        self,
        position
    ):
        self.player.setPosition(position)


# ============================================================
# VOLUME
# ============================================================

    def change_volume(
        self,
        value
    ):
        self.audio_output.setVolume(value / 100.0)


# ============================================================
# POSITION
# ============================================================

    def position_changed(
        self,
        position
    ):

        self.slider.setValue(position)
        self.position_label.setText(
            self.format_time(position)
        )


# ============================================================
# DURATION
# ============================================================

    def duration_changed(
        self,
        duration
    ):

        self.slider.setRange(0, duration)
        self.duration_label.setText(
            self.format_time(duration)
        )


# ============================================================
# PLAYBACK STATE
# ============================================================

    def playback_state_changed(
        self,
        state
    ):

        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("❚❚ PAUSE")
        else:
            self.play_button.setText("▶ PLAY")


# ============================================================
# FORMAT TIME
# ============================================================

    @staticmethod
    def format_time(
        milliseconds
    ):

        total_seconds = int(milliseconds / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes:02d}:{seconds:02d}"
