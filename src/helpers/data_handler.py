import csv

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets
import copy
import flammkuchen as fl
from scipy.io.wavfile import write
import sounddevice as sd
import os
import datetime
import time

from .region_item import RegionItem


class DataHandler(QtWidgets.QFrame):
    """
    Class that handles all annotated data within one DataFrame.
    """
    def __init__(self, data: dict, labels: dict, log: list = []):
        super().__init__()
        self.data = data
        self.labels = labels
        self.audio_player = None

        self.regions = None
        self.plots = None
        self.key_currently_selected_audio = None
        self.max_duration = None

        # Dict where all actions are logged (add/remove/change)
        self.log = log

        # QTableWidget object will be initialized in class TableWidget and set here then
        self.table_widget = None

        # QFrame objects that will be initialized in class AnnotatePreciseWidget and set here then
        self.annotate_precise_widget = None

        # dataframe that saves all annotations
        # Initial saves the pos of the upper audio player (--> not really relevant, maybe omit)
        self.table_data = pd.DataFrame(columns=['Initial', 'From', 'To', 'Event', 'Selected', 'Regions', 'Comment'])

    ##################################################################################
    # Load/Save data
    ##################################################################################
    def load_annotations(self, df):
        """
        Method for loading annotations from a .csv-file.
        """
        self.table_data = df
        self.table_data['Selected'] = False
        regions = []
        for idx in range(len(self.table_data)):
            regions_ = []
            for plot in self.plots:
                region = RegionItem()

                region.setRegion([self.table_data.loc[idx, 'From'], self.table_data.loc[idx, 'To']])
                region.setMovable(False)
                region.sigRegionChanged.connect(self.change_selected_region)
                plot.addItem(region)
                regions_.append(region)
            regions.append(regions_)
        self.table_data['Regions'] = regions

        # this can be removed later but is important to be compatible with old .airway files
        if 'Comment' not in self.table_data.columns:
            self.table_data['Comment'] = ['' for _ in range(len(self.table_data))]

        # sort values
        self.table_data = self.table_data.sort_values(by=['From'], ignore_index=True)
            
        self.reload_table()

    def save(self, path):
        """
        Method for saving all data to a .airway-file.
        """
        df = copy.deepcopy(self.table_data)
        data = copy.deepcopy(self.data)
        del df['Regions']
        del df['Selected']

        for key in data.keys():
            del data[key]['t']
            del data[key]['data']

        d = {'Data_Information': data, 'Annotations_DataFrame': df, 'Labels': self.labels, 'Log': self.log}
        fl.save(path, d)

    def save_annotated_events_wav(self, path, annotations_file_name):
        """
        Method for saving all annotated events to .wav-files.
        """
        if self.key_currently_selected_audio is None:
            self.table_widget.main_window.show_error_messagebox("Annotated events can only be exported "
                                                                "from .wav or .mp3 files.")
            return

        events = self.table_data['Event'].unique()
        for event in events:
            class_path = os.path.join(path, f'{event}_{annotations_file_name}')
            os.mkdir(class_path)
            idx = 0
            for index, row in self.table_data.iterrows():
                if row['Event'] == event:
                    sampling_rate = self.data[self.key_currently_selected_audio]['sampling_rate']
                    try:
                        data = self.data[self.key_currently_selected_audio]['data'][int(row['From'] * sampling_rate):int(row['To'] * sampling_rate), ...]
                    except:
                        continue
                    write(filename=os.path.join(class_path, f"{event}_{idx}.wav"), rate=sampling_rate, data=data)
                    idx += 1

            # check if no .wav was saved --> if yes, remove the folder because we don't need it
            if len(os.listdir(class_path)) == 0:
                os.rmdir(class_path)

    def save_annotated_events_csv(self, path):
        """
        Method for saving all annotated events to .csv-files.
        """
        df = copy.deepcopy(self.table_data)
        for index, row in df.iterrows():
            seconds_from = str(datetime.timedelta(seconds=row["From"]))
            seconds_to = str(datetime.timedelta(seconds=row["To"]))
            df.loc[index, 'From'] = seconds_from + f" ({row['From']})"
            df.loc[index, 'To'] = seconds_to + f" ({row['To']})"

        del df['Regions']
        del df['Selected']
        del df['Initial']
        df.to_csv(path, sep=';')

    def save_log(self, path):
        """
        Method for saving the log to a .csv-file.
        """
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.log[0].keys(), delimiter=';')
            writer.writeheader()
            writer.writerows(self.log)

    ##################################################################################
    # General methods
    ##################################################################################
    def contains_audio_file(self):
        """
        Check if any of the items in the dictionary contain a path to a WAV or MP3 file.

        Returns:
        True if at least one item contains a path to a WAV or MP3 file, False otherwise.
        """
        for key, entry in self.data.items():
            path = entry['path']
            if ".wav" in path or ".mp3" in path:
                return True
        return False

    ##################################################################################
    # Methods that modify the DataFrame through window events
    ##################################################################################
    def add_event(self):
        """
        Method adds an event ('yellow' event).
        """
        # check if any row is selected --> if yes, no new event can be added until the row in unselected again
        for index, row in self.table_data.iterrows():
            if bool(row['Selected']) is True:
                return

        # get current position/region and add a new event there
        if self.audio_player is not None:
            pos = self.audio_player.position() / 1000
        else:
            pos = None
        min_x, max_x = self.regions[0].getRegion()

        regions = []
        for plot in self.plots:
            region = RegionItem()
            region.setRegion([min_x, max_x])
            region.setMovable(False)
            region.sigRegionChanged.connect(self.change_selected_region)
            plot.addItem(region)
            regions.append(region)

        self.table_data = pd.concat([self.table_data, pd.DataFrame([
                {'Initial': pos, 'From': min_x, 'To': max_x, 'Event': '', 'Selected': False,
                 'Regions': regions, 'Comment': ''}])], ignore_index=True)

        self.log.append({'Timestamp': time.time(), 'Action': "ADD", 'From': min_x, 'To': max_x,
                         'Event': '', 'Comment': ''})

        # save last row (which is the one we just added) in a variable
        # to scroll there later after we sorted the DataFrame
        last_row = self.table_data.iloc[-1]

        # sort values
        self.table_data = self.table_data.sort_values(by=['From'], ignore_index=True)

        self.table_widget.reload_table()

        # scroll to the row that we just added
        for index, row in self.table_data.iterrows():
            if row.equals(last_row):
                self.table_widget.scroll_to_index(index)

    def add_precise_event(self, event_idx):
        """
        Method adds a precisely annotated event ('green' event).
        """
        # first check if we want to annotate an already selected region
        for index, row in self.table_data.iterrows():
            if bool(row['Selected']) is True:
                self.table_data.loc[index, 'Event'] = self.labels['classes'][event_idx]
                self.reload_table()
                self._update_region(self.table_data.loc[index, 'Regions'])
                self.table_widget.scroll_to_index(index)
                return

        # if not, the normal region will be used to annotate the selected region
        try:
            pos = self.audio_player.position()
        except:
            pos = None
        min_x, max_x = self.regions[0].getRegion()

        if min_x == max_x:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText('Please select a region.')
            msg.setWindowTitle("Error")
            msg.exec_()
            return

        regions = []
        for plot in self.plots:
            region = RegionItem()
            region.setRegion([min_x, max_x])
            region.setMovable(False)
            region.sigRegionChanged.connect(self.change_selected_region)
            plot.addItem(region)
            regions.append(region)

        self.table_data = pd.concat([self.table_data, pd.DataFrame([{'Initial': pos, 'From': min_x, 'To': max_x,
             'Event': self.labels['classes'][event_idx], 'Selected': False, 'Regions': regions, 'Comment': ''}])],
            ignore_index=True)

        self.log.append({'Timestamp': time.time(), 'Action': "ADD_precise", 'From': min_x, 'To': max_x,
                         'Event': self.labels['classes'][event_idx], 'Comment': ''})

        # save last row (which is the one we just added) in a variable
        # to scroll there later after we sorted the DataFrame
        last_row = self.table_data.iloc[-1]

        # sort values
        self.table_data = self.table_data.sort_values(by=['From'], ignore_index=True)

        self.reload_table()

        # scroll to the row that we just added
        for index, row in self.table_data.iterrows():
            if row.equals(last_row):
                self.table_widget.scroll_to_index(index)

    def delete_selected_row(self):
        """
        Deletes a selected table entry from the DataFrame.
        """
        for index, row in self.table_data.iterrows():
            if row['Selected'] is True:
                reply = QtWidgets.QMessageBox.question(self, 'Delete', f'Do you want to delete the selected row? \n '
                                                                       f'Event: {row["Event"]}',
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                                                       QtWidgets.QMessageBox.Yes)
                if reply != QtWidgets.QMessageBox.Yes:
                    return

                for plot in self.plots:
                    for region in self.table_data.loc[index, 'Regions']:
                        plot.removeItem(region)
                self.table_data = self.table_data.drop(index)
                self.table_data = self.table_data.reset_index(drop=True)
                self.unselect_all()
                self.reload_table()
                self.log.append({'Timestamp': time.time(), 'Action': "REMOVE",
                                 'From': self.table_data.loc[index, 'From'], 'To': self.table_data.loc[index, 'To'],
                                 'Event': self.table_data.loc[index, 'Event'], 'Comment': ''})
                break

    def reload_table(self):
        """
        Reloading the GUI table.
        """
        self.table_widget.reload_table()

    def play_selected_region(self):
        """
        Method for playing the selected region.
        """
        if self.key_currently_selected_audio is None:
            return
        elif self.audio_player is not None:
            if self.audio_player.state() == self.audio_player.PlayingState:
                return

        min_x, max_x = self.regions[0].getRegion()
        for index, row in self.table_data.iterrows():
            if row['Selected'] is True:
                min_x = row['From']
                max_x = row['To']

        data = self.data[self.key_currently_selected_audio]['data']
        sampling_rate = self.data[self.key_currently_selected_audio]['sampling_rate']
        data_to_play = data[int(min_x * sampling_rate):int(max_x * sampling_rate)]
        if len(data_to_play) == 0:
            return

        sd.stop()
        sd.play(data_to_play, sampling_rate, blocking=False)

    def change_selected_region(self):
        """
        Method that changes the values within the DataFrame when the boundaries of the selected region are changing.
        """
        region = self.sender()
        min_x, max_x = region.getRegion()

        if min_x < 0:
            min_x = 0
        if max_x > self.max_duration:
            max_x = self.max_duration

        for index, row in self.table_data.iterrows():
            if row['Selected'] is True:
                self.table_data.loc[index, 'From'] = min_x
                self.table_data.loc[index, 'To'] = max_x

                for regions_ in row['Regions']:
                    regions_.setRegion([min_x, max_x])

                # sort values
                self.table_data = self.table_data.sort_values(by=['From'], ignore_index=True)

                self.reload_table()
                break

    def select_previous_or_next_event(self, x):
        """
        Method for selecting the previous or next annotated event (when clicking the corresponding button/key)
        """
        if len(self.table_data) == 0:
            return

        currently_selected = None
        for index, row in self.table_data.iterrows():
            if bool(row['Selected']) is True:
                currently_selected = index
                break

        if currently_selected is None:
            if x == -1:
                return
            else:
                new_index = 0
        else:
            new_index = currently_selected + x
            if new_index == -1:
                self.reload_table()
                return
            elif new_index >= len(self.table_data):
                new_index = len(self.table_data) - 1

        self.unselect_all()
        self.table_widget.select_row(new_index)
        sd.stop()

    def unselect_all(self):
        """
        Method for unselecting all events within the table. (I just do it for all entries to keep everything clean)
        """
        for index, row in self.table_data.iterrows():
            for region in row['Regions']:
                region.setMovable(False)
            self._update_region(row['Regions'])

        self.set_regions_visible(True)
        self.set_regions_movable(True)
        self.table_data.loc[:, 'Selected'] = False
        self.reload_table()

    @staticmethod
    def _update_region(regions):
        """
        Set visible false and true as workaround to update the regions color inside the PyGraphItem.
        """
        for region in regions:
            region.setVisible(False)
            region.setVisible(True)

    ##################################################################################
    # Methods to get data for Bar Graph Window
    ##################################################################################
    def get_statistics_data(self, labels, flag='length'):
        """
        Method for getting the data for the bar graph window.
        """
        if flag != 'count' and flag != 'length':
            raise ValueError("Parameter 'flag' is not valid.")

        y_data = np.zeros(len(labels))
        for index, event in enumerate(labels):
            for _, row in self.table_data.iterrows():
                if row['Event'] == event:
                    if flag == 'count':
                        y_data[index] += 1
                    elif flag == 'length':
                        length = row['To'] - row['From']
                        y_data[index] += length

        return y_data

    def set_regions_movable(self, value):
        """
        Method for setting the regions movable or not.
        """
        for region in self.regions:
            region.setMovable(value)

    def set_regions_visible(self, value=True):
        """
        Method for setting the regions visible or not.
        """
        for region in self.regions:
            region.setVisible(value)


