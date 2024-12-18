from PyQt6 import QtWidgets, QtGui, QtCore
import os
from pathlib import Path
from pkg_resources import resource_filename
from src.helpers.data_handler import DataHandler


class PlayerButtonsWidget(QtWidgets.QWidget):
    """
    Class containing everything related to the buttons that control the media player.
    """
    def __init__(self, data_handler):
        """
        Constructor for the PlayerButtonsWidget class.
        """
        super().__init__()
        self.main_layout = QtWidgets.QHBoxLayout()
        self._data_handler: DataHandler = data_handler

        self.last_position = None  # position where the player was before playing a selected region

        self._audio_player = self._data_handler.audio_player
        self._audio_player.playbackStateChanged.connect(self._change_button_icon)

        self.play_icon = QtGui.QIcon(resource_filename(__name__, '../images/play.png'))
        self.stop_icon = QtGui.QIcon(resource_filename(__name__, '../images/stop.png'))
        forward_icon = QtGui.QIcon(resource_filename(__name__, '../images/forward.png'))
        backward_icon = QtGui.QIcon(resource_filename(__name__, '../images/backward.png'))

        button_functions = [self.backward_five_sec, self.toggle_play, self.forward_five_sec]
        button_icons = [backward_icon, self.play_icon, forward_icon]
        self.buttons = []
        self.main_layout.addStretch()
        for function, icon in zip(button_functions, button_icons):
            button = QtWidgets.QPushButton(icon, '')
            button.setIconSize(QtCore.QSize(35, 35))
            button.clicked.connect(function)
            self.main_layout.addWidget(button)

            self.buttons.append(button)

        self.main_layout.addStretch()
        self.main_layout.setSpacing(5)
        self.setLayout(self.main_layout)

    def toggle_play(self):
        """
        Event-method for starting/pausing playing the audio through the media player.
        """
        # check if there is a region selected
        for _, row in self._data_handler.table_data.iterrows():
            if row['Selected'] is True:
                # check if the player is already playing
                if self._audio_player.playbackState() == self._audio_player.PlaybackState.PlayingState:
                    self._audio_player.pause()
                else:
                    # if there is a region selected, save the position where the player currently is
                    if self.last_position is None:
                        self.last_position = self._audio_player.position()

                    # set information of when the player should stop
                    # as we are playing a selected region, we need to set the end position of the region as the stop
                    self.parent().current_end_position = row['To']

                    self._audio_player.setPosition(row['From'] * 1000)
                    self._audio_player.play()
                self._data_handler.set_regions_movable(False)
                self._data_handler.set_regions_visible(False)
                self._data_handler.reload_table()
                return
        
        # The following code is only executed if there is no region selected
        # So check if there is a previous position saved and set to that position
        self.set_player_to_last_position()

        # Start or stop playing the audio
        if self._audio_player.playbackState() == self._audio_player.PlaybackState.PlayingState:
            self._audio_player.pause()
            self._data_handler.set_regions_movable(True)
            self._data_handler.set_regions_visible(True)
        else:
            self._audio_player.play()
            self._data_handler.set_regions_movable(False)
        self._data_handler.set_regions_visible(True)
        self._data_handler.table_data.loc[:, 'Selected'] = False
        self._data_handler.reload_table()

    def set_player_to_last_position(self):
        """ 
        Method for setting the player to the last position when unselecting a region.
        """
        if self.last_position is not None:
            self._audio_player.setPosition(self.last_position)
            self.last_position = None
            self.parent().current_end_position = None

    def _change_button_icon(self, state):
        """
        Event-method for changing the start/pause button icon when clicked.
        """
        if state == self._audio_player.PlaybackState.PlayingState:
            self.buttons[1].setIcon(self.stop_icon)
        else:
            self.buttons[1].setIcon(self.play_icon)

    def forward_five_sec(self):
        """
        Event-method for skipping 5 seconds forward.
        """
        new_pos = self._audio_player.position() + 5000
        if new_pos < self._audio_player.duration():
            self._audio_player.setPosition(new_pos)
        else:
            self._audio_player.setPosition(self._audio_player.duration())
        self._data_handler.unselect_all()

    def backward_five_sec(self):
        """
        Event-method for skipping 5 seconds backward.
        """
        self._audio_player.setPosition(self._audio_player.position() - 5000)
        self._data_handler.unselect_all()


class PlayerBarWidget(QtWidgets.QProgressBar):
    """
    Class containing everything related to the media player progress bar.
    """
    timestamp_updated = QtCore.pyqtSignal(str)

    def __init__(self, audio_player):
        super().__init__()
        self._audio_player = audio_player
        self._audio_player.positionChanged.connect(self.update_position)

        self.current_end_position = None

        self.setTextVisible(False)
        self.setRange(0, 1000)
        self.setFixedHeight(25)
        self.dragging = False

        self._init_style_sheet()

    def update_position(self, milliseconds: int) -> None:
        """
        Method for continuously updating the progress bar when using the media player.
        """
        if self._audio_player.duration():
            self.setValue((milliseconds / self._audio_player.duration()) * self.maximum())
            duration = int(milliseconds / 1000)
            seconds = str(duration % 60)
            minutes = str(duration // 60) 
            self.timestamp_updated.emit(minutes.zfill(2) + ':' + seconds.zfill(2))

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Event-method for updating the progress bar when clicking on it.
        """
        self.dragging = True
        value = (event.position().x() / self.width()) * self.maximum()
        self._audio_player.setPosition((event.position().x() / self.width()) * self._audio_player.duration())
        self.setValue(value)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Event-method for updating the progress bar when dragging the mouse.
        """
        if self.dragging:
            x = event.position().x()
            if event.position().x() > self.width():
                x = self.width()
            value = (x / self.width()) * self.maximum()
            self._audio_player.setPosition((x / self.width()) * self._audio_player.duration())
            self.setValue(value)

    def mouseReleaseEvent(self, event):
        """
        Event-method for updating the progress bar when releasing the mouse.
        """
        self.dragging = False

    def enterEvent(self, event: QtCore.QEvent) -> None:
        """
        Event-method for changing the style sheet when hovering over the progress bar.
        """
        self.setStyleSheet(
            """
            QProgressBar {
                margin-top: 10px;
                margin-bottom: 10px;
                height: 5px;
                border: 0px solid #555;
                border-radius: 2px;
                background-color: black;
            }
            QProgressBar::chunk {
                background-color: lightGreen;
                border-radius: 2px;
                width: 1px;
            }
            """
        )

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """
        Event-method for changing the style sheet when not hovering over the progress bar.
        """
        self._init_style_sheet()

    def _init_style_sheet(self):
        """
        Method for initializing the style sheet of the progress bar.
        """
        self.setStyleSheet(
            """
            QProgressBar {
                margin-top: 10px;
                margin-bottom: 10px;
                height: 5px;
                border: 0px solid #555;
                border-radius: 2px;
                background-color: black;
            }
            QProgressBar::chunk {
                background-color: white;
                border-radius: 2px;
                width: 1px;
            }
            """
        )
