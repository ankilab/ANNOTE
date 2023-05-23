from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent, QMediaResource
from PyQt5 import QtCore
import numpy as np
import wave
import tempfile


class AudioPlayer(QMediaPlayer):
    def __init__(self, data_handler):
        """
        Class for playing audio files.
        """
        super().__init__(flags=QMediaPlayer.VideoSurface)
        self.data_handler = data_handler
        self.playlist = QMediaPlaylist()

        self.setNotifyInterval(20)

    def set_new_data(self, path):
        """
        Loading a new file that can be played using the audio player.

        Currently it is only possible to play .wav and .mp3 files. Data from .csv files is not easily loadable into
        the QMediaPlayer class.
        """
        if ".wav" in path or ".mp3" in path:
            content = QMediaContent(QtCore.QUrl.fromLocalFile(str(path)))
            self.playlist.removeMedia(0)
            self.playlist.addMedia(content)
            self.setPlaylist(self.playlist)
        else:
            raise Exception("QMediaPlayer can only play .wav or .mp3 files.")
