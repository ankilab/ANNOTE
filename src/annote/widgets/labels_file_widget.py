from PyQt6 import QtWidgets, QtGui, QtCore
import os
import json


class LabelsFileWindow(QtWidgets.QWidget):
    """
    Class containing everything to generate or modify the "labels_file.json".
    """
    def __init__(self, main_window):
        """
        Initialize the window.
        """
        super(LabelsFileWindow, self).__init__()
        self.main_window = main_window

        self.invalid_shortcuts = ["P", "S"]
        self.shortcut_regex = QtCore.QRegularExpression("[A-Z0-9]")
        self.labels_dict = {}

        self.init_ui()

        # Always load labels from labels file first, afterwards from labels property in data_handler
        settings_path = self.main_window.settings.value("labels_file")
        if settings_path is not None:
            self.file_path_text_box.setText(settings_path)
        elif self.main_window.data_handler is not None:
            labels = self.main_window.data_handler.labels
            for label, shortcut in zip(labels["classes"], labels["shortcuts"]):
                self.labels_dict[label] = shortcut
            self.reload_table()

    def init_ui(self):
        """
        Initialize the UI.
        """
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)

        # Add layout for file loading
        self.file_path_layout = QtWidgets.QHBoxLayout()
        self.file_path_text_box = QtWidgets.QLineEdit("")
        self.file_path_text_box.textChanged.connect(self._file_path_text_box_changed)
        self.file_path_text_box.setEnabled(False)
        self.browse_file_button = QtWidgets.QPushButton("Load file")
        self.browse_file_button.clicked.connect(self._browse_file_button_clicked)
        self.file_path_layout.addWidget(self.file_path_text_box)
        self.file_path_layout.addWidget(self.browse_file_button)
        self.main_layout.addLayout(self.file_path_layout)
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.main_layout.addWidget(line)

        # Add label/shortcut layout
        self.add_labels_layout = QtWidgets.QVBoxLayout()
        self.add_labels_layout.addWidget(QtWidgets.QLabel("<b>Labels:</b>"))

        self.textboxes_layout = QtWidgets.QHBoxLayout()
        self.label_textbox = QtWidgets.QLineEdit("")
        self.label_textbox.setPlaceholderText("Label (e.g. 'dry_cough')")
        self.label_textbox.setFixedWidth(150)
        self.shortcut_textbox = QtWidgets.QLineEdit("")
        self.shortcut_textbox.setPlaceholderText("Shortcut (A-Z or 0-9)")
        self.shortcut_textbox.setFixedWidth(150)
        self.shortcut_textbox.setValidator(QtGui.QRegularExpressionValidator(self.shortcut_regex))

        self.textboxes_layout.addWidget(self.label_textbox)
        self.textboxes_layout.addWidget(self.shortcut_textbox)
        self.add_labels_layout.addLayout(self.textboxes_layout)

        self.add_label_button = QtWidgets.QPushButton("Add to table")
        self.add_label_button.clicked.connect(self.add_label_button_pressed)
        self.add_labels_layout.addWidget(self.add_label_button)
        self.main_layout.addLayout(self.add_labels_layout)

        self.labels_table = QtWidgets.QTableWidget()
        self.labels_table.setColumnCount(2)
        self.labels_table.setColumnWidth(0, 170)
        self.labels_table.setColumnWidth(1, 100)
        self.labels_table.setHorizontalHeaderLabels(['Label', 'Shortcut'])
        self.labels_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.labels_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)

        self.main_layout.addWidget(self.labels_table)

        self.remove_label_button = QtWidgets.QPushButton("Remove row")
        self.remove_label_button.setToolTip("Remove selected row")
        self.remove_label_button.clicked.connect(self.remove_selected_row)
        self.main_layout.addWidget(self.remove_label_button)

        ######################################################################
        # Save to file or apply changes to the main window
        ######################################################################
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.main_layout.addWidget(line)

        self.save_apply_layout = QtWidgets.QHBoxLayout()
        self.save_file_button = QtWidgets.QPushButton("Save to file")
        self.save_file_button.clicked.connect(self._save_file_button_clicked)
        self.apply_button = QtWidgets.QPushButton("Apply changes")
        self.apply_button.setToolTip("Apply the changes made to be shown in the annotation window")
        self.apply_button.clicked.connect(self._apply_button_clicked)
        self.save_apply_layout.addWidget(self.save_file_button)
        if self.main_window.initialized:
            self.save_apply_layout.addWidget(self.apply_button)

        self.main_layout.addLayout(self.save_apply_layout)

        self.setLayout(self.main_layout)
    
    def _browse_file_button_clicked(self):
        """
        Open a file dialog to select a labels file.
        """
        dialog = QtWidgets.QFileDialog()
        dialog.setDefaultSuffix("json")
        dialog.setNameFilter("ANNOTE label file (*.json)")

        if dialog.exec():
            selected_file = dialog.selectedFiles()[0]
            self.file_path_text_box.setText(selected_file)

    def _file_path_text_box_changed(self):
        """
        Check if the file path is valid and load the file if it is.
        """
        path = self.file_path_text_box.text()
        if not os.path.exists(path):
            with open(path, 'w') as f:
                d = {"classes": [], "shortcuts": {}}
                json.dump(d, f, indent=2)
        
        if ".json" in path:
            self.clear_labels()
            self.clear_table()
            self.load_file(path)
        
    def add_label_button_pressed(self):
        """
        Add the label and shortcut to the table.
        """
        if self.shortcut_textbox.text() in self.invalid_shortcuts:
            self.show_error_messagebox(f"Can't use {self.shortcut_textbox.text()} as shortcut since it is "
                                       f"already used for an ANNOTE functionality.")
        elif self.shortcut_textbox.text() == "" or self.label_textbox.text() == "":
            self.show_error_messagebox("Label/Shortcut textbox can't be empty.")
            return
        else:
            # Check if the shortcut is already used and return if yes
            for _, value in self.labels_dict.items():
                if value == self.shortcut_textbox.text():
                    self.show_error_messagebox("Shortcut already used.")
                    return
                
            # Add Label and Shortcut to the table
            self.labels_dict[self.label_textbox.text()] = self.shortcut_textbox.text()
            self.label_textbox.setText("")
            self.shortcut_textbox.setText("")
            self.reload_table()

    def _apply_button_clicked(self):
        """
        Apply the changes made to the main window.
        """
        d = {'classes': [], 'shortcuts': []}
        for key, value in self.labels_dict.items():
            d['classes'].append(key)
            d['shortcuts'].append(value)

        self.main_window.data_handler.labels = d
        self.main_window.annotate_buttons_widget.reload_classes_buttons()
        if self.main_window.annotation_statistics_window is not None:
            self.main_window.close_annotation_statistics_window()
            self.main_window.open_annotation_statistics_window()
        self.main_window.init_shortcuts()
        self.main_window.update()

        path = self.file_path_text_box.text()
        if path != "":
            self._save_file_button_clicked()
        else:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle('Applying')
            msg.setText("Applying successful.")
            msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
            msg.exec()

    def reload_table(self):
        """
        Reload the table with the labels and shortcuts.
        """
        self.clear_table()
        self.labels_table.setHorizontalHeaderLabels(['Label', 'Shortcut'])
        for key, value in self.labels_dict.items():
            row = self.labels_table.rowCount()
            self.labels_table.insertRow(row)
            self.labels_table.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
            self.labels_table.setItem(row, 1, QtWidgets.QTableWidgetItem(value))
    
    def clear_table(self):
        """
        Clear the table.
        """
        self.labels_table.clear()
        self.labels_table.setRowCount(0)
        
    def clear_labels(self):
        """
        Clear the labels dictionary.
        """
        self.labels_dict = {}

    def load_file(self, path):
        """
        Load the labels from a file.
        """
        if os.path.exists(path):
            try:
                with open(path) as f:
                    labels_file = json.load(f)

                wrong_shortcuts = []
                for label, shortcut in zip(labels_file["classes"], labels_file["shortcuts"]):
                    if shortcut in self.invalid_shortcuts or not self.shortcut_regex.match(shortcut, 0, QtCore.QRegularExpression.MatchType.NormalMatch):
                        wrong_shortcuts.append(shortcut)
                    self.labels_dict[label] = shortcut

                if len(wrong_shortcuts) > 0:
                    self.show_error_messagebox(f"Shortcuts '{wrong_shortcuts}' in file \n '{path}'\n are not allowed or too short/too long.\n\n Please change it to a single capital letter or number.")

                self.reload_table()
            except Exception as e:
                self.show_error_messagebox(f"A error occured: {str(e)}.")
        else:
            self.show_error_messagebox("File does not exist.")

    def remove_selected_row(self):
        """
        Remove the selected row from the table.
        """
        row_index = self.labels_table.currentRow()
        try:
            row_values = [self.labels_table.item(row_index, i).text() for i in range(self.labels_table.columnCount())]
        except:
            self.show_error_messagebox("No table entry selected.")
            return
        self.labels_dict = {key: value for key, value in self.labels_dict.items() if not (key == row_values[0] and value == row_values[1])}

        self.reload_table()
        
    def _save_file_button_clicked(self):
        """
        Save the labels to a file.
        """
        path = self.file_path_text_box.text()
        if path == "":
            dialog = QtWidgets.QFileDialog()
            dialog.setDefaultSuffix("json")
            dialog.setNameFilter("ANNOTE label file (*.json)")

            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                selected_file = dialog.selectedFiles()[0]
                path = selected_file

        if not os.path.exists(path):
            with open(path, 'w') as f:
                d = {"classes": [], "shortcuts": {}}
                json.dump(d, f, indent=2)

        if os.path.exists(path):
            # Check if the file is empty --> don't have to ask for override then
            with open(path) as f:
                labels_file = json.load(f)
            if not len(labels_file["classes"]) == 0:
                reply = QtWidgets.QMessageBox.question(self, 'Save', f'Do you want to override the file at location \n {path}?',
                                                       QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel,
                                                       QtWidgets.QMessageBox.StandardButton.Yes)
                if not reply == QtWidgets.QMessageBox.StandardButton.Yes:
                    return

            d = {'classes': [], 'shortcuts': []}
            for key, value in self.labels_dict.items():
                d['classes'].append(key)
                d['shortcuts'].append(value)

            with open(path, 'w') as f:
                json.dump(d, f, indent=2)

            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle('Saving')
            msg.setText("Saving successful.")
            msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
            msg.exec()
        else:
            self.show_error_messagebox(f"Labels file path {path} does not exist.")

    def show_error_messagebox(self, error_msg):
        """
        Show a error messagebox.
        """
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Error')
        msg.setText(error_msg)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        msg.exec()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        Close the window and save the path of the labels file.
        """
        # Set the path of the labels file to the path that was opened when this window was closed,
        # as it is likely that this is the file that should be used
        self.main_window.settings.setValue("labels_file", self.file_path_text_box.text())
        self.close()

        