from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtGui import QPalette, QColor, QShortcut
from PyQt6.QtCore import Qt
import sys
from pathlib import Path
import flammkuchen as fl
import os
from datetime import datetime
from pkg_resources import resource_filename


import widgets
import helpers


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        """
        Initializes the main window of the application.
        """
        super(MainWindow, self).__init__()
        self.directory = None
        self.filename = None
        self.initialized = False
        self.save_path = None

        self.settings = QtCore.QSettings("ANKI_LAB", "ANNOTE")
        self.settings.setValue("labels_file", None)

        # open dialog to find out if the user wants to load new data or continue on previous loaded data
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("&File")
        self.menu_file.addAction("Import", self._open_import_window)
        self.menu_file.addAction("Open (.annote)", self._open)
        self.menu_file.addAction("Save", self._save)
        self.menu_file.addAction("Close/Exit", self._close)

        self.menu_extras = self.menu.addMenu("&Extras")
        self.labels_file_action = QtGui.QAction("Create/modify labels", self)
        self.labels_file_action.triggered.connect(self.open_labels_file_window)
        self.menu_extras.addAction(self.labels_file_action)

        self.annotation_statistics_action = QtGui.QAction("Annotation Statistics", self)
        self.annotation_statistics_action.triggered.connect(self.open_annotation_statistics_window)
        self.annotation_statistics_action.setCheckable(True)
        self.menu_extras.addAction(self.annotation_statistics_action)

        self.menu_extras.addAction("Export Annotations (.csv)", self._export_annotated_events_csv)
        self.menu_extras.addAction("Export Annotations (.wav)", self._export_annotated_events_wav)
        self.menu_extras.addAction("Export Log (.txt)", self._export_log)

        # variables for "Extras" menu point
        self.labels_file_window = None
        self.annotation_statistics_window = None

        # init some variables
        self.data_handler = None
        self.audio_player = None

        self.setGeometry(200, 150, 1300, 800)
        self.setWindowTitle("ANNOTE - Annotation of Time-series Events")

        self.logo_path = resource_filename(__name__, 'images/logo.png')
        self.setWindowIcon(QtGui.QIcon(self.logo_path))

    def _init_ui(self):
        """
        Initializes the user interface of the main window.

        This function creates and sets up all the necessary widgets and layouts for the main window. It also initializes the audio player and data handler objects, and sets up their interdependencies.

        The following widgets are created and added to the main layout:
        * PlayerControls: a widget that displays player controls (play/pause/stop).
        * AnnotatePreciseWidget: a widget that allows the user to annotate precise labels on the audio waveform by clicking and dragging.
        * TableWidget: a widget that displays a table of the audio files in the dataset, along with their annotations.

        If the UI has already been initialized, this function does nothing.

        Returns:
        --------
        None
        """

        # create main layouts/widgets
        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QGridLayout()

        if self.data_handler.contains_audio_file():
            # create audio player and data handler objects
            self.audio_player = helpers.AudioPlayer(self.data_handler)
            self.data_handler.audio_player = self.audio_player

            # add player controls widget
            self.player = widgets.PlayerControls(self.data_handler)
            self.main_layout.addWidget(self.player, 2, 0, 1, 1)
        else:
            self.player = None
            self.audio_player = None
            self.data_handler.audio_player = None

        # add annotate precise widget
        self.annotate_precise_widget = widgets.AnnotatePreciseWidget(self.audio_player, self.data_handler)
        self.main_layout.addWidget(self.annotate_precise_widget, 0, 0, 2, 3)

        # add annotate buttons widget
        self.annotate_buttons_widget = widgets.AnnotateButtonsWidget(self.data_handler)
        if self.data_handler.contains_audio_file():
            self.main_layout.addWidget(self.annotate_buttons_widget, 3, 0, 1, 1)
        else:
            self.main_layout.addWidget(self.annotate_buttons_widget, 2, 0, 2, 1)

        # add table widget
        table_widget = widgets.TableWidget(self.audio_player, self.data_handler, self.annotate_precise_widget, self)
        self.data_handler.table_widget = table_widget
        self.main_layout.addWidget(table_widget, 2, 1, 2, 2)
        self.main_layout.setAlignment(table_widget, Qt.AlignmentFlag.AlignRight)

        # initialize keyboard shortcuts
        self.init_shortcuts()

        # set main layout and central widget
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

    ##################################################################################
    # Menu controls
    ##################################################################################

    def _open_import_window(self):
        """
        Import and load a new file.

        If the user has made any unsaved changes, prompt them to save before importing a new file.

        After selecting a file, initialize or reset the UI and data handler to reflect the new data.

        Returns:
        --------
        None
        """
        if self._ask_save() is False:
            return

        self.import_window = widgets.ImportWindow(self)
        self.import_window.setWindowTitle("ANNOTE - Load data")
        self.import_window.setWindowIcon(QtGui.QIcon(self.logo_path))
        self.import_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.import_window.setFixedWidth(500)
        self.import_window.show()

    def load_main_window(self, data, labels):
        if len(data) == 0:
            self.show_error_messagebox("No data loaded.")

        if self.initialized is False:
            self.data_handler = helpers.DataHandler(data, labels)
            self._init_ui()
            self.initialized = True
        else:
            self.save_path = None
            for i in reversed(range(self.main_layout.count())):
                self.main_layout.itemAt(i).widget().setParent(None)
            self.data_handler = helpers.DataHandler(data, labels)
            self._init_ui()

    def _open(self):
        """
        Open and load a new .annote file.
        """
        if self._ask_save() is False:
            return

        fn = QtWidgets.QFileDialog.getOpenFileName(self, "Open and load new .annote file",
                                                   directory=str(self.directory) if self.directory else "",
                                                   filter="*.annote")[0]
        if not fn:
            return

        annote_file_path = Path(fn)
        self.save_path = annote_file_path

        df = fl.load(str(annote_file_path))

        # Load labels file
        labels = df['Labels']

        # Log dictionary
        log = df['Log']

        # Load data
        data = {}
        for idx, key in enumerate(df['Data_Information'].keys()):
            entry = df['Data_Information'][key]
            file_path = entry['path']
            if not os.path.exists(file_path):
                file_path = self._select_correct_file(file_path, f"File at location '{file_path}' does not exist! "
                                                                 f"Please select a valid file.")

            if helpers.get_md5_hash(entry['path']) != entry['hash']:
                    file_path = self._select_correct_file(file_path,  f"File at location '{file_path}' is not the "
                                                                      f"same as the saved one! "
                                                                      f"Please select the same file.")

            if ".wav" in file_path or ".mp3" in file_path:
                d = helpers.data_loading.load_wav_mp3_file(file_path, entry['channel'])
            elif ".csv" in file_path:
                d = helpers.data_loading.load_csv_file(file_path, entry['t_column_name'], entry['data_column_name'])
            else:
                self.show_error_messagebox("Error when loading data files.")
                return

            if type(d) == str:
                self.show_error_messagebox(d)
            else:
                data[f'{idx}'] = d

        # Load annotations
        if self.initialized is False:
            self.data_handler = helpers.DataHandler(data, labels, log)
            self._init_ui()
            self.data_handler.load_annotations(df['Annotations_DataFrame'])
            self.initialized = True
        else:
            self.save_path = None
            for i in reversed(range(self.main_layout.count())):
                self.main_layout.itemAt(i).widget().setParent(None)
            self.data_handler = helpers.DataHandler(data, labels, log)
            self._init_ui()
            self.data_handler.load_annotations(df['Annotations_DataFrame'])

    @staticmethod
    def _select_correct_file(path, message):
        """
        Open a file dialog to allow the user to select a correct file.
        """
        # show an error message
        QtWidgets.QMessageBox.critical(None, "Error", message)
        file_extension = Path(path).suffix

        # open a file dialog to allow the user to select a correct file
        new_filepath, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select a file", "", f"*{file_extension}")
        return new_filepath

    def _save(self):
        """
        Save the current annotations to the current save path.
        """
        if self.initialized is False:
            self.show_error_messagebox("Please load and annotate data first.")
            self.annotation_statistics_action.setChecked(False)
            return

        if self.save_path is None:
            fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Annotations',
                                                       directory=str(
                                                           self.directory) + '/' + self.filename if self.directory else self.filename,
                                                       filter="*.annote")[0]
            if not fn:
                return False
            self.save_path = fn
        else:
            reply = QtWidgets.QMessageBox.question(self, 'Save', f'Save to file {Path(self.save_path).name}?',
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                                                   QtWidgets.QMessageBox.StandardButton.Yes)
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Annotations',
                                                           directory=str(
                                                               self.directory) + '/' + self.filename if self.directory else self.filename,
                                                           filter="*.annote")[0]
                if not fn:
                    return False
                self.save_path = fn
        self.data_handler.save(self.save_path)
        self.saving_successful_messagebox(self.save_path)
        return True

    def _close(self):
        """
        Close the application.
        """
        self.close_annotation_statistics_window()
        if not self._ask_save():
            return
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Close the application.
        """
        self.close_annotation_statistics_window()
        if not self._ask_save():
            a0.ignore()

    ##################################################################################
    # Extras
    ##################################################################################
    def open_labels_file_window(self):
        """
        Opens the LabelsFileWindow for generating or modifying labels. Passes the script path as an argument.

        Returns:
        --------
        None
        """
        if self.labels_file_window is not None:
            self.labels_file_window.show()
            return

        self.labels_file_window = widgets.LabelsFileWindow(self)
        self.labels_file_window.setWindowTitle("ANNOTE - Create/modify labels")
        self.labels_file_window.setWindowIcon(QtGui.QIcon(self.logo_path))
        self.labels_file_window.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.labels_file_window.setFixedWidth(300)
        self.labels_file_window.setFixedHeight(300)
        self.labels_file_window.show()

    def open_annotation_statistics_window(self):
        """
        Opens the annotation statistics window.

        If data is not loaded, an error message is displayed, and the action is unchecked.

        If the annotation statistics window is not already open, it is created, and its properties
        are set. If the window is already open, it is closed.

        Returns:
        --------
        None
        """
        if self.initialized is False:
            self.show_error_messagebox("Please load data first.")
            self.annotation_statistics_action.setChecked(False)
            return

        if self.annotation_statistics_window is None:
            self.annotation_statistics_action.setChecked(True)
            self.annotation_statistics_window = widgets.AnnotationsStatisticsWindow(self)
            self.annotation_statistics_window.setFixedSize(600, 800)
            self.annotation_statistics_window.setWindowTitle("ANNOTE - Annotation Statistics")
            self.annotation_statistics_window.setWindowIcon(QtGui.QIcon(self.logo_path))
            self.annotation_statistics_window.show()
        else:
            self.close_annotation_statistics_window()

    def close_annotation_statistics_window(self):
        """
        Closes the annotation statistics window.

        If the annotation statistics window is open, this function will close it and set the
        `annotation_statistics_window` variable to `None`.

        """
        if self.annotation_statistics_window is not None:
            self.annotation_statistics_action.setChecked(False)
            self.annotation_statistics_window.close()
            self.annotation_statistics_window = None

    def update_annotation_statistics_window(self):
        """
        Updates the annotation statistics window.
        """
        if self.annotation_statistics_window is not None:
            self.annotation_statistics_window.reload_graph()

    def _export_annotated_events_csv(self):
        """
        Export the annotated events to a .csv file.
        """
        if self.initialized is False:
            self.show_error_messagebox("Please load data first.")
            return

        fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Export Annotations as .csv',
                                                   directory=str(
                                                       self.directory) + '/' + self.filename if self.directory else self.filename,
                                                   filter="*.csv")[0]
        if not fn:
            return
        # save all events to the created folder
        self.data_handler.save_annotated_events_csv(fn)
        self.saving_successful_messagebox(fn)

    def _export_annotated_events_wav(self):
        """
        Export the annotated events to a .wav file.
        """
        if self.initialized is False:
            self.show_error_messagebox("Please load data first.")
            self.annotation_statistics_action.setChecked(False)
            return

        fn = QtWidgets.QFileDialog.getExistingDirectory(self, 'Export Annotations as .wav',
                                                        directory=str(self.directory) if self.directory else "")
        if not fn:
            return

        # since we need the name of our file where we save the annotations,
        # we have to make sure it was already saved before
        if self.save_path is None:
            self.show_error_messagebox(
                f'Please save your annotations first before exporting the events as .wav files. ')
            return

        # create new folder
        folder_name = "Annotated_Events_" + str(datetime.now().strftime("%d%m%Y_%H%M%S"))
        path = os.path.join(fn, folder_name)
        os.mkdir(path)

        # save all events to the created folder
        self.data_handler.save_annotated_events_wav(path, Path(self.save_path).name.split('.')[0])
        self.saving_successful_messagebox(path)

    def _export_log(self):
        """
        Export the log to a .txt file.
        """
        if self.initialized is False:
            self.show_error_messagebox("Please annotate data first.")
            return

        fn = QtWidgets.QFileDialog.getSaveFileName(self, 'Save annotationg log as .txt',
                                                   directory=str(
                                                       self.directory) + '/' + self.filename if self.directory else self.filename,
                                                   filter="*.txt")[0]
        if not fn:
            return

        self.data_handler.save_log(fn)
        self.saving_successful_messagebox(fn)

    def saving_successful_messagebox(self, path):
        """
        Shows a message box that the saving was successful.
        """
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Saving')
        msg.setText(f'Saved successfully to \n "{path}"')
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setWindowIcon(QtGui.QIcon(self.logo_path))
        msg.exec()

    ##################################################################################
    # Helper
    ##################################################################################

    def show_error_messagebox(self, error_msg):
        """
        Shows a message box with an error message.
        """
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setText(error_msg)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.setWindowIcon(QtGui.QIcon(self.logo_path))
        msg.exec()

    def _ask_save(self):
        """
        Asks the user if he wants to save the current annotations.
        """
        if self.initialized:
            reply = QtWidgets.QMessageBox.question(self, 'Save', 'Do you want to save?',
                                                   QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No | QtWidgets.QMessageBox.StandardButton.Cancel,
                                                   QtWidgets.QMessageBox.StandardButton.Yes)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                return self._save()
            elif reply == QtWidgets.QMessageBox.StandardButton.Cancel:
                return False
            elif reply == QtWidgets.QMessageBox.StandardButton.No:
                reply = QtWidgets.QMessageBox.question(self, 'Save', 'Are you sure that you want to close without '
                                                                     'saving? (Unsaved content will get lost!)',
                                                       QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                                                       QtWidgets.QMessageBox.StandardButton.No)
                if reply == QtWidgets.QMessageBox.StandardButton.No:
                    return False
        return True

    ##################################################################################
    # Shortcuts
    ##################################################################################

    def init_shortcuts(self):
        """
        Initializes all shortcuts.
        """
        # Remove all shortcuts
        for shortcut in self.findChildren(QShortcut):
            shortcut.setEnabled(False)

        # Add all shortcuts
        keys_and_functions = [(Qt.Key.Key_Return, self._add_event), (Qt.Key.Key_Left, self._previous_event),
                              (Qt.Key.Key_Right, self._next_event), (Qt.Key.Key_P, self._play_region),
                              (Qt.Key.Key_S, self._stop_region), (Qt.Key.Key_Delete, self._delete_row),
                              (Qt.Key.Key_Backspace, self._delete_row), ("Ctrl+S", self._save)]
        if self.player is not None:
            keys_and_functions.append((Qt.Key.Key_Space, self.player.player_buttons_widget.toggle_play))

        for (key, function) in keys_and_functions:
            event = QShortcut(QtGui.QKeySequence(key), self)
            event.activated.connect(function)
            event.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)

        # add shortcuts defined in setup.json to GUI
        for shortcut in self.data_handler.labels['shortcuts']:
            event = QShortcut(QtGui.QKeySequence(shortcut), self)
            event.activated.connect(self._add_precise_event)
            event.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)

    def _add_event(self):
        self.data_handler.add_event()

    def _delete_row(self):
        self.data_handler.delete_selected_row()

    def _play_region(self):
        self.annotate_precise_widget.play_region()

    def _stop_region(self):
        self.annotate_precise_widget.stop_region()

    def _previous_event(self):
        self.data_handler.select_previous_or_next_event(-1)

    def _next_event(self):
        self.data_handler.select_previous_or_next_event(+1)

    def _add_precise_event(self):
        pressed_key = self.sender().key().toString()
        idx = 0
        for shortcut in self.data_handler.labels['shortcuts']:
            if pressed_key == shortcut:
                self.data_handler.add_precise_event(event_idx=idx)
            else:
                idx += 1


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


def init_style(app):
    """
    Method uses a Palette to change the whole window style to dark mode.
    """
    palette = QPalette()
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)


def main():
    """
    Main method to start the GUI.
    """
    sys.excepthook = except_hook
    app = QtWidgets.QApplication(sys.argv)
    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")
    init_style(app)
    gui = MainWindow()
    gui.show()
    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
