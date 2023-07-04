from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput #, QMediaContent #, QMediaPlaylist
from PyQt6 import QtCore
import numpy as np


class AudioPlayer(QMediaPlayer):
    def __init__(self, data_handler):
        """
        Class for playing audio files.
        """
        super().__init__()
        self.data_handler = data_handler

        self._audio_output = QAudioOutput()
        self.setAudioOutput(self._audio_output)

    def set_new_data(self, data):
        """
        Loading a new file that can be played using the audio player.

        Currently it is only possible to play .wav and .mp3 files. Data from .csv files is not easily loadable into
        the QMediaPlayer class as it can't handle QByteArrays.
        """
        path = data['path']
        if ".csv" in path:
            raise NotImplementedError("Currently it is not possible to play .csv files using the audio player.")
        
        qurl = QtCore.QUrl.fromLocalFile(data['path'])
        self.setSource(qurl)
