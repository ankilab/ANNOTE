import re
import numpy as np
import librosa
import pandas as pd
import json
import re

from .calculate_md5_hash import get_md5_hash


def load_wav_mp3_file(path, channel):
    """
    Load wav or mp3 file and return dictionary with data, sampling rate, duration, time axis and hash.
    """
    d = {'path': path}
    try:
        data, sampling_rate = librosa.load(path, sr=None, mono=False)
        d['sampling_rate'] = sampling_rate
    except Exception as e:
        raise RuntimeError(f"Can't load the file {path}: str({e})")

    d['channel'] = channel
    if channel == "Single channel":
        d['data'] = data
    elif channel == "Left channel":
        data = np.transpose(data)
        d['data'] = data[..., 0]
    elif channel == "Right channel":
        data = np.transpose(data)
        d['data'] = data[..., 1]
    elif channel == "Average of channels":
        d['data'] = librosa.to_mono(data)
    else:
        raise RuntimeError(f"Option {channel} was not defined.")

    # Add duration and time axis (x-axis)
    d['duration'] = len(d['data']) / d['sampling_rate']
    d['t'] = np.linspace(0, len(d['data']) / d['sampling_rate'], len(d['data']))

    d['hash'] = get_md5_hash(path)
    return d


def load_csv_file(path, t_column_name, data_column_name):
    """
    Load csv file and return dictionary with data, time axis, duration and hash.
    """
    d = {'path': path, 't_column_name': t_column_name, 'data_column_name': data_column_name}

    # Load selected time axis column from csv
    try:
        df = pd.read_csv(path, usecols=[t_column_name])

        df[t_column_name] = pd.to_datetime(df[t_column_name], errors='coerce')
        
        if df[t_column_name].notna().all():
            d['t_labels'] = df[t_column_name].copy()
            df[t_column_name] = (df[t_column_name] - df[t_column_name].iloc[0]).dt.total_seconds()

        d['t'] = df[t_column_name].dropna().to_numpy()

        # Load selected data column from csv
        df = pd.read_csv(path, usecols=[data_column_name])
        d['data'] = df[data_column_name].dropna().to_numpy()
    except Exception as e:
        raise RuntimeError(f"Can't load the file {path}: str({e})")

    d['duration'] = duration = d['t'][-1]
    d['hash'] = get_md5_hash(path)
    return d


def load_labels(path):
    """
    Load labels from json file.
    """
    try:
        with open(path) as f:
            labels = json.load(f)
        if len(labels['classes']) == 0:
            return "Labels file doesn't contain any labels."
    except Exception as e:
        raise RuntimeError(f"Can't load the file {path}: str({e})")
    return labels


def load_wav_mp3_file_metadata(path):
    """
    Load wav or mp3 file and return dictionary with sampling rate, duration and number of channels.
    """
    try:
        data, sampling_rate = librosa.load(path, sr=None, mono=False)
        data = np.transpose(data)
        duration = int(len(data) / sampling_rate)
        num_channels = data.shape[1] if data.ndim == 2 else 1
    except Exception as e:
        raise RuntimeError(f"Can't load the file {path}: str({e})")
    d = {'sampling_rate': sampling_rate, 'duration': duration, 'num_channels': num_channels}
    return d


def load_csv_metadata(path, delimiter=","):
    """
    Load csv file and return dictionary with number of columns, number of rows and column names.
    """
    with open(path) as f:
        w = f.readline()
    w_sep = w.split(delimiter)

    cols = []
    for col in w_sep:
        col = re.sub(r"\n", "", col)
        cols.append(col)
    return cols
