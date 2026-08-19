from pathlib import Path

from PySide6.QtCore import Signal, QUrl, Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSlider


class MP3Player(QWidget):
    play_started = Signal(str)
    stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self._delegate_player = self._find_parent_player(parent)

        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.playbackStateChanged.connect(self.playback_state_changed)
        self.player.errorOccurred.connect(self._player_error)
        self.player.mediaStatusChanged.connect(self._media_status)
        self.build_ui()

    @staticmethod
    def _find_parent_player(parent):
        """Find the application's already-working central MP3Player."""
        widget = parent
        while widget is not None:
            candidate = getattr(widget, "mp3_player", None)
            if isinstance(candidate, MP3Player) and candidate is not widget:
                return candidate
            try:
                widget = widget.parentWidget()
            except AttributeError:
                widget = None

        # MP3 Showcase can be created outside the normal parent chain.
        # In that case use the application's existing central player.
        try:
            active = QApplication.activeWindow()
            while active is not None:
                candidate = getattr(active, "mp3_player", None)
                if isinstance(candidate, MP3Player) and candidate is not active:
                    return candidate
                try:
                    active = active.parentWidget()
                except AttributeError:
                    active = None
        except RuntimeError:
            pass

        # Last resort: locate an existing MP3Player among live widgets.
        try:
            for widget in QApplication.allWidgets():
                if isinstance(widget, MP3Player) and widget is not parent:
                    return widget
        except RuntimeError:
            pass

        return None

    def _player_error(self, error, error_string):
        print("========================================")
        print("MP3 PLAYER ERROR")
        print("ERROR:", error)
        print("MESSAGE:", error_string)
        print("SOURCE:", self.player.source().toString())
        print("========================================")
        self.track_label.setText("MP3 ERROR: " + str(error_string or error))

    def _media_status(self, status):
        print("MP3 MEDIA STATUS:", status)

    def build_ui(self):
        self.setObjectName("mp3Player")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self.track_label = QLabel("Geen track geladen")
        self.track_label.setObjectName("playerTrack")
        layout.addWidget(self.track_label)

        controls = QHBoxLayout()
        controls.setSpacing(6)
        self.play_button = QPushButton("PLAY")
        self.play_button.setMinimumWidth(90)
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)
        self.stop_button = QPushButton("STOP")
        self.stop_button.setMinimumWidth(90)
        self.stop_button.clicked.connect(self.stop)
        controls.addWidget(self.stop_button)
        self.position_label = QLabel("00:00")
        controls.addWidget(self.position_label)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.seek)
        controls.addWidget(self.slider, 1)
        self.duration_label = QLabel("00:00")
        controls.addWidget(self.duration_label)
        layout.addLayout(controls)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)

        self.setStyleSheet("""
            QWidget#mp3Player { background-color:#181818; border-top:1px solid #333333; }
            QLabel { background:transparent; color:#cccccc; }
            QLabel#playerTrack { color:#ffffff; font-size:14px; font-weight:bold; }
            QPushButton { background-color:#252525; color:#ffffff; border:1px solid #444444; border-radius:5px; padding:6px 12px; }
            QPushButton:hover { background-color:#333333; }
            QSlider::groove:horizontal { background:#333333; height:5px; border-radius:2px; }
            QSlider::handle:horizontal { background:#dddddd; width:12px; margin:-4px 0; border-radius:6px; }
        """)

    def play_file(self, path):
        if not path:
            return
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            self.track_label.setText("MP3 niet gevonden: " + str(file_path))
            print("MP3 NIET GEVONDEN:", file_path)
            return
        if not file_path.is_file():
            self.track_label.setText("Geen geldig MP3-bestand: " + str(file_path))
            print("GEEN BESTAND:", file_path)
            return

        self.current_path = str(file_path)
        self.track_label.setText(file_path.name)

        if self._delegate_player is not None:
            print("MP3 SHOWCASE -> CENTRALE MP3 PLAYER:", self.current_path)
            self._delegate_player.play_file(self.current_path)
        else:
            print("MP3 PLAY:", self.current_path)
            self.player.stop()
            self.player.setPosition(0)
            url = QUrl.fromLocalFile(self.current_path)
            print("MP3 URL:", url.toString())
            self.player.setSource(url)
            self.player.play()

        self.play_started.emit(self.current_path)

    def toggle_play(self):
        if self._delegate_player is not None:
            self._delegate_player.toggle_play()
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.current_path:
            self.player.play()

    def stop(self):
        if self._delegate_player is not None:
            self._delegate_player.stop()
        else:
            self.player.stop()
        self.slider.setValue(0)
        self.position_label.setText("00:00")
        self.stopped.emit()

    def seek(self, position):
        if self._delegate_player is not None:
            self._delegate_player.seek(position)
        else:
            self.player.setPosition(position)

    def change_volume(self, value):
        if self._delegate_player is not None:
            self._delegate_player.change_volume(value)
        else:
            self.audio_output.setVolume(value / 100.0)

    def position_changed(self, position):
        self.slider.setValue(position)
        self.position_label.setText(self.format_time(position))

    def duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))

    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("PAUSE")
        else:
            self.play_button.setText("PLAY")

    @staticmethod
    def format_time(milliseconds):
        total_seconds = int(milliseconds / 1000)
        return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"
