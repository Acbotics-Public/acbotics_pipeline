"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract
from .data_container import DataContainer
import numpy as np
import math


class DataContainer_FFT(DataContainer):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(self, data, start_time):
        if isinstance(data, list):
            # print("converting list to array")
            data = np.array(data)
        # todo. This should hold meta data about frequency bins and such
        self.data = data
        self.start_time = start_time

    def get_timestamps(self):
        return [self.start_time]

    def is_constant_rate(self):
        return False

    def get_start_time(self):
        return self.start_time

    def get_timestamped_data(self):
        return (self.start_time,)

    def get_end_time(self):
        """Returns the time of the last sample"""
        return self.start_time
