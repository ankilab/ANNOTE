from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtMultimedia import QMediaPlayer
import pyqtgraph as pg
import datetime
import time


class TableWidget(QtWidgets.QWidget):
    """
    Class containing everything for displaying annotated events inside a TableWidget.
    """

    def __init__(self, audio_player: QMediaPlayer, data_handler, annotate_precise_widget, main_window):
        """
        Constructor for TableWidget.
        """
        super().__init__()
        self._audio_player = audio_player
        self._data_handler = data_handler
        self.annotate_precise_widget = annotate_precise_widget
        self.main_window = main_window

        self.start_currently_selected_region = None
        self.stop_currently_selected_region = None

        self.main_layout = QtWidgets.QVBoxLayout()

        self.table = QtWidgets.QTableWidget()
        self.table.setMinimumWidth(600)
        self.table.setColumnCount(5)
        self.table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setHorizontalHeaderLabels([" ", "From", "To", "Event", "Comment"])
        self.table.cellClicked.connect(self.select_row)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # configure header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self._data_handler.table_widget = self.table
        self.main_layout.addWidget(self.table)

        self.buttons_container = QtWidgets.QHBoxLayout()
        add_comment_button = QtWidgets.QPushButton('Add comment to selected row')
        add_comment_button.clicked.connect(self._add_comment)
        self.buttons_container.addWidget(add_comment_button)

        delete_button = QtWidgets.QPushButton('(Del) - Delete selected row')
        delete_button.clicked.connect(self._delete_selected_row)
        self.buttons_container.addWidget(delete_button)

        self.main_layout.addLayout(self.buttons_container)
        self.setLayout(self.main_layout)

    def select_row(self, row):
        """
        Method for selecting a specific row depending on the row index.
        """
        if self._audio_player is not None:
            if self._audio_player.playbackState() == self._audio_player.PlaybackState.PlayingState:
                return

        df = self._data_handler.table_data
        row_of_interest_selected = bool(df.loc[row, 'Selected'])
        self._data_handler.unselect_all()
        if row_of_interest_selected is True:
            df.loc[row, 'Selected'] = False
            for region in df.loc[row, 'Regions']:
                region.setMovable(False)
            self.start_currently_selected_region = None
            self.stop_currently_selected_region = None

            # set player to the last position before an event was selected
            self.main_window.player.player_buttons_widget.set_player_to_last_position()
        else:
            df.loc[row, 'Selected'] = True
            for region in df.loc[row, 'Regions']:
                region.setMovable(True)
            self._data_handler.set_regions_visible(False)
            self._data_handler.set_regions_movable(False)

            self.start_currently_selected_region = df.loc[row, 'From']
            self.stop_currently_selected_region = df.loc[row, 'To']

        self.reload_table()

    @staticmethod
    def set_region_brush(region, color):
        """
        Method for setting the brush of a region.
        """
        region.setBrush(pg.mkColor(color))
        region.setHoverBrush(pg.mkColor(color))

    def _clear_table(self):
        """
        Method for removing all table entries.
        """
        while self.table.rowCount() > 0:
            self.table.removeRow(0)
        self.table.setRowCount(0)

    def reload_table(self):
        """
        Method for reloading the whole table.
        Therefore, the DataFrame of the DataHandler is used everytime since there are all information.
        """
        self._clear_table()

        index_to_scroll_to = None  # for table scrolling if a region is selected

        # iterate over the whole DataFrame
        for index, row in self._data_handler.table_data.iterrows():
            i = self.table.rowCount()
            self.table.setRowCount(i + 1)

            checkbox = QtWidgets.QTableWidgetItem()
            self.table.setItem(i, 0, checkbox)

            seconds_from = str(datetime.timedelta(seconds=row["From"]))[:-4]
            seconds_to = str(datetime.timedelta(seconds=row["To"]))[:-4]

            item = QtWidgets.QTableWidgetItem(seconds_from)
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 1, item)
            item = QtWidgets.QTableWidgetItem(seconds_to)
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 2, item)

            if not row['Event']:
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem('---'))
                color = QtGui.QColor(238, 233, 108)
                for region in row['Regions']:
                    self.set_region_brush(region, (238, 233, 108, 150))
            else:
                color = QtGui.QColor(87, 223, 151)
                for region in row['Regions']:
                    self.set_region_brush(region, (87, 223, 151, 150))

            if row['Selected'] is True:
                index_to_scroll_to = index
                self.table.item(i, 0).setBackground(QtGui.QColor(204, 97, 212))
                for region in row['Regions']:
                    self.set_region_brush(region, (204, 97, 212, 150))
            else:
                self.table.item(i, 0).setBackground(QtGui.QColor(255, 255, 255))

            # add current information to each region item because it is needed 
            # to let the region item identify on its own that it was selected
            for region in row['Regions']:
                region.table_data = self._data_handler.table_data
                region.table_widget = self

            item = QtWidgets.QTableWidgetItem(str(row["Event"]))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 3, item)

            item = QtWidgets.QTableWidgetItem(str(row["Comment"]))
            item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
            self.table.setItem(i, 4, item)

            for j in range(1, 5):
                self.table.item(i, j).setBackground(color)

        # update annotation statistics
        if self.main_window.annotation_statistics_action.isChecked():
            self.main_window.update_annotation_statistics_window()

        if index_to_scroll_to is not None:
            self.scroll_to_index(index_to_scroll_to)

    def scroll_to_index(self, index):
        """
        Method for scrolling to a specific row.
        """
        index_to_scroll = self.table.model().index(index, 0)
        self.table.scrollTo(index_to_scroll)

    def _add_comment(self):
        """
        Method for adding a comment to a specific row.
        """
        for index, row in self._data_handler.table_data.iterrows():
            if row['Selected'] is True:
                text, success = QtWidgets.QInputDialog.getText(self, 'Text Input Dialog', 'Comment:',
                                                               text=row['Comment'])
                if success:
                    self._data_handler.table_data.loc[index, 'Comment'] = text
                    self._data_handler.log.append({'Timestamp': time.time(), 'Action': "COMMENT",
                                                   'From': self._data_handler.table_data.loc[index, 'From'],
                                                   'To': self._data_handler.table_data.loc[index, 'To'],
                                                   'Event': self._data_handler.table_data.loc[index, 'Event'],
                                                   'Comment': [row['Comment'], text]})
                self.reload_table()
                return

        self.main_window.show_error_messagebox("No row selected.")

    def _delete_selected_row(self):
        """
        Method for deleting a specific row.
        """
        self._data_handler.delete_selected_row()
