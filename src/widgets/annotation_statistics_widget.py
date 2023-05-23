from PyQt5 import QtWidgets, QtGui, QtCore
import pyqtgraph as pg
import pandas as pd


class AnnotationsStatisticsWindow(QtWidgets.QWidget):
    """
    Class containing everything to display how many events were annotated yet.
    """
    def __init__(self, main_window):
        """
        Constructor of the class.
        """
        super(AnnotationsStatisticsWindow, self).__init__()
        self.main_window = main_window
        self.table = None
        self.flag = 'length'
        self.labels_from_table = pd.unique(self.main_window.data_handler.table_data['Event']
                                [self.main_window.data_handler.table_data['Event'] != ''])
        self.labels_from_file = self.main_window.data_handler.labels["classes"]
        self.labels = list(set(self.labels_from_table).union(self.labels_from_file))
        self.init_ui()

    def init_ui(self):
        """
        Method to initialize the user interface.
        """
        self.main_layout = QtWidgets.QVBoxLayout()

        buttons_layout = QtWidgets.QHBoxLayout()
        self.toggle_plot_button = QtWidgets.QPushButton("Toggle lengths/counts")
        self.toggle_plot_button.clicked.connect(self.toggle_plot_button_clicked)

        self.plot_label = QtWidgets.QLabel('Length')
        self.plot_label.setAlignment(QtCore.Qt.AlignCenter)
        self.plot_label.setStyleSheet("background-color: lightblue; color: black")

        buttons_layout.addWidget(self.toggle_plot_button)
        buttons_layout.addWidget(self.plot_label)
        self.main_layout.addLayout(buttons_layout)

        self.plot_widget = pg.GraphicsLayoutWidget()
        self.y_axis = pg.AxisItem(orientation='left', showValues=True)
        y = self.labels
        ydict = dict(enumerate(y))
        self.y_axis.setTicks([ydict.items()])

        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(len(self.labels))
        self.table.setVerticalHeaderLabels(self.labels[::-1])
        self.table.setColumnCount(1)
        self.table.horizontalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.plot = None
        self.reload_graph()

        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addWidget(self.table)

        self.setLayout(self.main_layout)

    def toggle_plot_button_clicked(self):
        """
        Method to toggle between length and count.
        """
        if self.flag == 'count':
            self.flag = 'length'
            self.plot_label.setText('Length')
            self.plot_label.setStyleSheet("background-color: lightblue; color: black")
        else:
            self.flag = 'count'
            self.plot_label.setText('Count')
            self.plot_label.setStyleSheet("background-color: lightgreen; color: black")
        self.reload_graph()

    def reload_graph(self):
        """
        Method to reload the graph.
        """
        if self.plot is not None:
            self.plot_widget.removeItem(self.plot)

        self.plot = self.plot_widget.addPlot(row=1, col=0, axisItems={'left': self.y_axis})

        x = self.main_window.data_handler.get_statistics_data(self.labels, self.flag)
        if max(x) != 0:
            x = x / max(x)

        if self.flag == 'count':
            self.bar_graph = pg.BarGraphItem(width=x, y=range(len(x)), x0=0, x1=1, height=0.8, brush=QtGui.QColor('lightgreen'))
        else:
            self.bar_graph = pg.BarGraphItem(width=x, y=range(len(x)), x0=0, x1=1, height=0.8, brush=QtGui.QColor('lightblue'))

        self.plot.addItem(self.bar_graph, ignoreBounds=True)

        y_range = len(self.labels)
        self.plot.setYRange(-1, y_range, padding=0)
        self.plot.setXRange(0, 1, padding=0)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideAxis('bottom')
        view_box = self.plot.getViewBox()
        view_box.setLimits(xMin=0, xMax=1, yMin=-1, yMax=10)

        # reload event count
        x = self.main_window.data_handler.get_statistics_data(self.labels, 'count')
        for idx in range(len(self.labels)):
            item = QtWidgets.QTableWidgetItem(str(int(x[::-1][idx])))
            self.table.setItem(idx-1, 1, item)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Method to close the window.
        """
        self.main_window.close_annotation_statistics_window()

