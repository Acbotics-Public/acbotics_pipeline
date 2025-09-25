"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract
from .data_container import DataContainer
import numpy as np
import math


class DataContainer_Beamformed_Output_1D(DataContainer):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(self, data, angles, start_time):
        if isinstance(data, list):
            # print("converting list to array")
            data = np.array(data)
        self.data = data
        self.start_time = start_time
        self.angles = angles

    def get_timestamps(self):
        return [
            self.start_time + i * 1e9 / self.sample_rate
            for i in range(self._calculate_data_length())
        ]

    def is_constant_rate(self):
        return False

    def get_start_time(self):
        return self.start_time

    def get_timestamped_data(self):
        return (self.start_time,)

    def get_end_time(self):
        """Returns the time of the last sample"""
        return self.start_time

    def get_angles(self):
        return self.angles
