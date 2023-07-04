from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from .player_widgets import PlayerButtonsWidget, PlayerBarWidget


class PlayerControls(QtWidgets.QFrame):
    """
    Class containing all buttons for playing audio files.
    """
    def __init__(self, data_handler):
        """
        Initialize the player controls.
        """
        super().__init__()
        self._data_handler = data_handler
        self._audio_player = self._data_handler.audio_player
        self._audio_player.positionChanged.connect(self.check_selected_region_continue_playing)
        self._init_ui()

        self._audio_player.durationChanged.connect(self.change_file)
        self.file_to_play_combo_box.setCurrentIndex(0)

        # variable to store the current end position of a selected region
        self.current_end_position = None

    @property
    def audio_player(self):
        """
        Returns the audio player that is used for playing the audio files.
        """
        return self._audio_player

    def _init_ui(self):
        """
        Initialize the UI of the player controls.
        """
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # add combo box for signal selection (i.e. the signal that is used for the player etc.)
        label = QtWidgets.QLabel("Select file for audio player:")
        self.main_layout.addWidget(label)

        self.file_to_play_combo_box = QtWidgets.QComboBox()
        for key in self._data_handler.data.keys():
            path = self._data_handler.data[key]['path']
            if ".wav" in path or ".mp3" in path:
                self.file_to_play_combo_box.addItem(f"{key}, {path}")
        self.file_to_play_combo_box.currentIndexChanged.connect(self.file_to_play_combo_box_changed)
        self.file_to_play_combo_box_changed()
        self.main_layout.addWidget(self.file_to_play_combo_box)

        # create player buttons
        self.player_buttons_widget = PlayerButtonsWidget(self._data_handler)
        self.main_layout.addWidget(self.player_buttons_widget)

        # create player bar and time labels
        container_layout = QtWidgets.QHBoxLayout()
        self.current_position = QtWidgets.QLabel("00:00")
        container_layout.addWidget(self.current_position)

        # add player bar
        self.player_bar_widget = PlayerBarWidget(self._audio_player)
        self.player_bar_widget.timestamp_updated.connect(self.current_position.setText)
        container_layout.addWidget(self.player_bar_widget)

        # add end position label
        self.end_position = QtWidgets.QLabel()
        container_layout.addWidget(self.end_position)

        self.main_layout.addLayout(container_layout)
        self.main_layout.addStretch()

        event_button = QtWidgets.QPushButton(' (Enter) - Event')
        event_button.setStyleSheet("QPushButton {border-style: outset; border-width: 2px; border-radius: 12px; "
                                   "border-color: black; padding: 4px; background-color: #DBDBDB; color: black}"
                                   "QPushButton::hover {background-color: yellow;}"
                                   )
        event_button.setFixedWidth(170)
        event_button.setFixedHeight(50)
        event_button.clicked.connect(self.event_button_clicked)
        self.main_layout.addWidget(event_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

    def change_file(self):
        """
        Method updates the end position time label (right to the progress bar) when a new file is loaded.
        """
        duration = int(self._audio_player.duration() / 1000)
        seconds = str(duration % 60)
        minutes = str(duration // 60)
        self.end_position.setText(minutes.zfill(2) + ':' + seconds.zfill(2))

    def event_button_clicked(self):
        """
        Event-method that adds a new 'yellow'-event to the table when clicked.
        """
        self._data_handler.add_event()

    def file_to_play_combo_box_changed(self):
        """
        Event-method that changes the player when the file selection changes.
        """
        if len(self.file_to_play_combo_box.currentText()) < 1:
            return
        key_, path_ = self.file_to_play_combo_box.currentText().split(", ")
        for key in self._data_handler.data.keys():
            if key == key_:
                path = self._data_handler.data[key]['path']
                if path == path_:
                    self._data_handler.key_currently_selected_audio = key
                    try:
                        self._audio_player.set_new_data(self._data_handler.data[key])
                    except Exception as e:
                        raise RuntimeError(str(e))


    def check_selected_region_continue_playing(self, position: int):
        """
        Method for checking if the selected region is still selected and if so, continue playing.
        """
        if self.current_end_position is not None:
            if position >= self.current_end_position * 1000:
                self._audio_player.pause()
                self.player_buttons_widget.set_player_to_last_position()


