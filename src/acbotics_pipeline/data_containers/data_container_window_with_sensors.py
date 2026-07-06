"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract
from .data_container import DataContainer
import numpy as np
import math
from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp


class DataContainer_Window_With_Sensors(DataContainer):
    @icontract.require(
        lambda sample_rate: sample_rate > 0, "sample_rate must be positive"
    )
    @icontract.require(
        lambda start_time: isinstance(start_time, SensorTimestamp),
        "start_time must be SensorTimestamp",
    )
    def __init__(self, data, sample_rate, start_time, tick_time=0, sensors={}):
        # TODO: MAke sure all data is 2D array even if only one channel?
        if isinstance(data, list):
            if len(data) > 0:
                if isinstance(data[0], list):
                    data = np.array(data)
                else:
                    data = np.array(data).reshape(1, -1)  # turn 1d into 2c
            else:
                data = np.array(data).reshape(
                    1, -1
                )  # turn 1d into 2c even though empty
        self.data = data
        self.sample_rate = sample_rate
        self.start_time = start_time
        self.sensors = sensors
        self.orig_start_time = start_time
        self.removed_data_count = 0
        self.tick_time = tick_time

    def get_timestamps(self):
        t_step = 1e9 / self.sample_rate
        st = self.start_time
        return [
            st + np.timedelta64(int(i * t_step), "ns")
            for i in range(self._calculate_data_length())
        ]

    def _calculate_data_length(self):
        s = self.data.shape
        if len(s) == 1:
            return s[0]
        return s[1]

    def _calculate_num_channels(self):
        s = self.data.shape
        if len(s) == 1:
            return 1
        return s[0]

    def is_constant_rate(self):
        return True

    @icontract.ensure(
        lambda result: isinstance(result, SensorTimestamp),
        "start_time must be SensorTimestamp",
    )
    def get_start_time(self):
        return self.start_time

    @icontract.ensure(lambda result: result > 0, "sample_rate must be positive")
    def get_sample_rate(self):
        return self.sample_rate

    def get_timestamped_data(self):
        return (self.get_timestamps(), self.data.transpose())

    @icontract.ensure(
        lambda result: isinstance(result, np.datetime64), "end_time must be datetime64"
    )
    def get_end_time(self):
        """Returns the time of the last sample"""
        td = (1.0e9 / self.sample_rate) * (self._calculate_data_length() - 1)
        return self.start_time + np.timedelta64(int(td), "ns")

    # def get_csv_header(self):
    #     return np.arange(self.data.shape[0])
