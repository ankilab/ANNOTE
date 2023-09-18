from PyQt6 import QtWidgets, QtGui, QtCore
import os
import json
from pathlib import Path
import glob

from src.helpers.data_loading import load_wav_mp3_file_metadata, load_csv_metadata, load_labels, \
    load_wav_mp3_file, load_csv_file


class ImportWindow(QtWidgets.QWidget):
    """
    Class containing everything to import data.
    """

    def __init__(self, main_window):
        super(ImportWindow, self).__init__()
        self.main_window = main_window
        self.channel_options = ["Left channel", "Right channel", "Average of channels"]
        self.init_ui()

        # Check if there is already a Labels file saved in the settings
        path = self.main_window.settings.value("labels_file")
        self.label_file_text_box.setText(path)
        self.files_to_load_layouts = {}

    def init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout()

        # Layouts to select new files that should be loaded
        label = QtWidgets.QLabel("<b>Data Files:</b>")
        self.main_layout.addWidget(label)

        self.data_files_layout = QtWidgets.QHBoxLayout()
        self.data_file_text_box = QtWidgets.QLineEdit()
        browse_data_file_button = QtWidgets.QPushButton("Browse")
        browse_data_file_button.clicked.connect(self._browse_data_file_button_clicked)
        add_data_file_button = QtWidgets.QPushButton("Add")
        add_data_file_button.clicked.connect(self._add_data_file_button_clicked)
        self.data_files_layout.addWidget(self.data_file_text_box)
        self.data_files_layout.addWidget(browse_data_file_button)
        self.data_files_layout.addWidget(add_data_file_button)

        self.selected_files_layout = QtWidgets.QVBoxLayout()
        self.selected_files_layout.addLayout(self.data_files_layout)
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.selected_files_layout.addWidget(line)
        self.main_layout.addLayout(self.selected_files_layout)

        # Layout to select the labels file that should be used
        label = QtWidgets.QLabel("<b>Labels File:</b>")
        self.main_layout.addWidget(label)
        self.label_files_layout = QtWidgets.QHBoxLayout()
        self.label_file_text_box = QtWidgets.QLineEdit()
        self.label_file_text_box.setEnabled(False)
        browse_labels_file_button = QtWidgets.QPushButton("Browse")
        browse_labels_file_button.clicked.connect(self._browse_labels_file_button_clicked)
        modify_labels_file_button = QtWidgets.QPushButton("Create/Modify")
        modify_labels_file_button.clicked.connect(self._modify_labels_file_button_clicked)
        self.label_files_layout.addWidget(self.label_file_text_box)
        self.label_files_layout.addWidget(browse_labels_file_button)
        self.label_files_layout.addWidget(modify_labels_file_button)

        self.main_layout.addLayout(self.label_files_layout)

        # Add button that loads all the selected files and starts the main widget afterwards
        load_button = QtWidgets.QPushButton("Load")
        load_button.clicked.connect(self._load_button_clicked)
        self.main_layout.addWidget(load_button)

        self.setLayout(self.main_layout)

    def _browse_data_file_button_clicked(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setOptions(QtWidgets.QFileDialog.Option.ReadOnly)
        dialog.setOptions(QtWidgets.QFileDialog.Option.ShowDirsOnly)

        file_name, _ = dialog.getOpenFileName(self,
                                              "Import and load new files",
                                              "",
                                              "Files (*.wav *.mp3 *.csv)")
        self.data_file_text_box.setText(file_name)

    def _add_data_file_button_clicked(self):
        path = self.data_file_text_box.text()
        layout = QtWidgets.QGridLayout()

        combo_box = []  # list containing one or two combo boxes
        if not os.path.exists(path):
            self.show_error_messagebox(f"File {path} does not exist.")
            return
        elif len(self.files_to_load_layouts) + 1 > 3:
            self.show_error_messagebox(f"Can't load more than three files.")
            return
        elif ".mp3" in path or ".wav" in path:
            combo_box_channel = QtWidgets.QComboBox()

            d = load_wav_mp3_file_metadata(path)

            # Information about the file and the data
            len_label = QtWidgets.QLabel(f"Duration (s): {d['duration']}")
            layout.addWidget(len_label, 1, 0)
            sr_label = QtWidgets.QLabel(f"Sampling rate (Hz): {d['sampling_rate']}")
            layout.addWidget(sr_label, 1, 1)

            # Combo box to let the user select the data they want to have displayed
            if d['num_channels'] == 2:
                for item in self.channel_options:
                    combo_box_channel.addItem(item)
            else:
                combo_box_channel.addItem("Single channel")

            # Add combo box
            layout.addWidget(combo_box_channel, 2, 0, 1, 2)
            combo_box.append(combo_box_channel)
        elif ".csv" in path:
            csv_combo_box_layout = QtWidgets.QGridLayout()
            time_column_label = QtWidgets.QLabel(f"Time Column:")
            data_column_label = QtWidgets.QLabel(f"Data Column:")
            time_column_combo_box = QtWidgets.QComboBox()
            data_column_combo_box = QtWidgets.QComboBox()

            csv_combo_box_layout.addWidget(time_column_label, 0, 0)
            csv_combo_box_layout.addWidget(time_column_combo_box, 0, 1)
            csv_combo_box_layout.addWidget(data_column_label, 1, 0)
            csv_combo_box_layout.addWidget(data_column_combo_box, 1, 1)

            cols = load_csv_metadata(path)
            for col in cols:
                time_column_combo_box.addItem(col)
                data_column_combo_box.addItem(col)

            # Add combo boxes to layout
            layout.addLayout(csv_combo_box_layout, 2, 0, 1, 2)
            combo_box.append(time_column_combo_box)
            combo_box.append(data_column_combo_box)
        else:
            raise NotImplementedError("File type is not implemented.")

        # Add filename to the layout
        fname_label = QtWidgets.QLabel(f"<b>{Path(path).name}</b>")
        layout.addWidget(fname_label, 0, 0, 1, 2)

        # Add remove button
        remove_button = QtWidgets.QPushButton("Remove")
        remove_button.clicked.connect(self._remove_file_entry)
        layout.addWidget(remove_button, 2, 2)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        layout.addWidget(line, 3, 0, 1, 3)

        self.files_to_load_layouts[remove_button] = {'layout': layout, 'path': str(path), 'combo_box': combo_box}
        self.selected_files_layout.addLayout(layout)
        self.data_file_text_box.setText("")

    def _remove_file_entry(self):
        layout = self.files_to_load_layouts[self.sender()]['layout']
        self._clear_layout(layout)
        self.files_to_load_layouts.__delitem__(self.sender())
        self.layout().removeItem(layout)
        layout.setParent(None)

    def _clear_layout(self, layout):
        """
        Removes all widgets and sublayouts from the given layout.

        Args:
            layout (QLayout): The layout to clear.
        """
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self._clear_layout(item.layout())
            del item

    def _browse_labels_file_button_clicked(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setOptions(QtWidgets.QFileDialog.Option.ReadOnly)
        dialog.setOptions(QtWidgets.QFileDialog.Option.ShowDirsOnly)

        # Check if we maybe find a labels file in the current directory
        file_path = None
        for file in glob.glob("**/*.json"):
            if "labels" in file:
                file_path = file
                #file_path = os.path.join(os.getcwd(), file)

        file_name, _ = dialog.getOpenFileName(self,
                                              "Select label file",
                                              "" if file_path is None else file_path,
                                              "ANNOTE label file (*.json)")
        # Check if the label file is valid
        if file_name == "":
            return

        with open(file_name, 'r') as f:
            labels = json.load(f)
            if not len(labels.keys()) == 2 or "classes" not in labels.keys() \
                    or "shortcuts" not in labels.keys() or len(labels["classes"]) != len(labels["shortcuts"]):
                self.show_error_messagebox("Labels file is not valid. It should contain an entry for "
                                           "classes and shortcuts.")
                return

        self.main_window.settings.setValue("labels_file", file_name)
        self.label_file_text_box.setText(file_name)

    def _modify_labels_file_button_clicked(self):
        self.main_window.open_labels_file_window()

    def _load_button_clicked(self):
        """
        Loads the data from the selected files and labels file.
        """
        # Check if there are any data files selected
        if len(self.files_to_load_layouts) == 0:
            self.show_error_messagebox("No data file selected.")
            return

        # Check if the labels file is valid
        labels_path = self.label_file_text_box.text()
        if labels_path == "" or ".json" not in labels_path:
            self.show_error_messagebox("Please specify a valid labels file.")
            return

        # Load labels
        labels = load_labels(labels_path)
        if type(labels) == str:
            self.show_error_messagebox(labels)
            return

        # Load all data files
        data = {}
        for idx, key in enumerate(self.files_to_load_layouts):
            entry = self.files_to_load_layouts[key]
            try:
                data[f'{idx}'] = self._get_data(entry)
            except Exception as e:
                self.show_error_messagebox(f"Error occured: {e}")
                return

        self.main_window.load_main_window(data, labels)
        self.close()

    def show_error_messagebox(self, error_msg):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setText(error_msg)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.exec()

    def _get_data(self, entry):
        """
        This method loads data dictionaries.
        """
        if ".wav" in entry['path'] or ".mp3" in entry['path']:
            return load_wav_mp3_file(entry['path'], entry['combo_box'][0].currentText())
        elif ".csv" in entry['path']:
            return load_csv_file(entry['path'], entry['combo_box'][0].currentText(),
                                 entry['combo_box'][1].currentText())
        else:
            self.show_error_messagebox("Error when loading data files.")
