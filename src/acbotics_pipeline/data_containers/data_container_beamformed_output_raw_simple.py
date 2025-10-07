"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract
from .data_container import DataContainer
import numpy as np


class DataContainer_Beamformed_Output_Raw_Simple(DataContainer):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(
        self,
        data,
        thetas,
        phis,
        frequencies,
        start_time,
    ):
        if isinstance(data, list):
            # print("converting list to array")
            data = np.array(data)
        self.data = data
        self.start_time = start_time
        self.thetas = thetas
        if isinstance(self.thetas, list):
            self.thetas = np.array(self.thetas, dtype=np.float64)
        self.phis = phis
        if isinstance(self.phis, list):
            self.phis = np.array(self.phis, dtype=np.float64)

        self.frequencies = frequencies
        if isinstance(self.frequencies, list):
            self.frequencies = np.array(self.frequencies, dtype=np.float64)

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

    def get_thetas(self):
        return self.thetas

    def get_phis(self):
        return self.phis
