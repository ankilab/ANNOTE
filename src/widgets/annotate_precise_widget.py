from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np

from .annotate_buttons_widget import AnnotateButtonsWidget


class AnnotatePreciseWidget(QtWidgets.QFrame):
    """
    Class containing the plot and the region that can be arbitrarily slided by the user.
    """
    def __init__(self, audio_player, data_handler):
        super().__init__()
        if audio_player is not None:
            self._audio_player = audio_player
            self._audio_player.positionChanged.connect(self.update_region_from_player)
        self.data_handler = data_handler
        self.data_handler.annotate_precise_widget = self

        self.init_ui()

    def init_ui(self):
        """
        Initialize the UI.
        """
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.plot_widget = pg.GraphicsLayoutWidget()

        # Add all plots
        self.max_duration = 0
        self.plots = []
        for idx, key in enumerate(self.data_handler.data.keys()):
            entry = self.data_handler.data[key]
            plot = self.plot_widget.addPlot(row=idx+1, col=0)
            plot.setYRange(-max(entry['data']), max(entry['data']), padding=0)
            plot.setMouseEnabled(x=True, y=False)
            self.plots.append(plot)

            if self.data_handler.data[key]['duration'] > self.max_duration:
                self.max_duration = self.data_handler.data[key]['duration']

            if len(self.plots) > 0:
                plot.setXLink(self.plots[idx - 1])

        # Set size policy
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_widget.setSizePolicy(sizePolicy)
        self.main_layout.addWidget(self.plot_widget)

        # region that can be arbitrarily slided by the user
        self.regions = []
        for _ in range(len(self.data_handler.data.keys())):
            region = pg.LinearRegionItem()
            region.setRegion([0, 0.025 * self.max_duration])
            region.setBrush(pg.mkColor((102, 102, 255, 255)))  # 160, 160, 160
            region.setHoverBrush(pg.mkColor((102, 102, 255, 255)))
            self.regions.append(region)

        for plot, region in zip(self.plots, self.regions):
            plot.addItem(region, ignoreBounds=True)
            region.sigRegionChanged.connect(self.update_regions)

        self.annotate_buttons_widget = AnnotateButtonsWidget(self.data_handler)
        self.main_layout.addWidget(self.annotate_buttons_widget)

        self.setLayout(self.main_layout)

        for plot, key in zip(self.plots, self.data_handler.data.keys()):
            t = self.data_handler.data[key]['t']
            data = self.data_handler.data[key]['data']

            plot.plot(t, data, pen=(255, 153, 0))
            plot.setXRange(0, self.max_duration)
            range_ = plot.getViewBox().viewRange()
            plot.getViewBox().setLimits(xMin=range_[0][0], xMax=range_[0][1],
                                        yMin=range_[1][0], yMax=range_[1][1])
            plot.setDownsampling(True, True)
            plot.setClipToView(True)
            plot.hideAxis('left')
            plot.hideAxis('bottom')

        self.data_handler.regions = self.regions
        self.data_handler.plots = self.plots
        self.data_handler.max_duration = self.max_duration

    def update_region_from_player(self):
        """
        Method called continuously when playing through the media player.
        """
        pos = self._audio_player.position() / 1000
        for region in self.regions:
            region.setRegion([pos - 0.0025 * self.max_duration, pos + 0.0025 * self.max_duration])

    def update_regions(self):
        """
        Method called when changing the region boundaries inside pyqtgraph widget.
        """
        sender_region = self.sender()
        for region in self.regions:
            if region == sender_region:
                min_x, max_x = region.getRegion()
                if min_x < 0:
                    min_x = 0
                if max_x > self.max_duration:
                    max_x = self.max_duration
                region.setRegion([min_x, max_x])
                break

        for region in self.regions:
            if region != sender_region:
                region.setRegion([min_x, max_x])

    def play_region(self):
        """
        Event-method called when the user wants to play the currently selected region.
        """
        self.annotate_buttons_widget.play_region()

    def stop_region(self):
        """
        Event-method called when the user wants to stop the audio playback of the currently selected region.
        """
        self.annotate_buttons_widget.stop_region()
