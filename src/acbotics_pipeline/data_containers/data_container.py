"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract


class DataContainer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_timestamps(self):
        pass

    @abstractmethod
    def is_constant_rate(self):
        pass

    @abstractmethod
    def get_start_time(self):
        pass

    def get_timestamped_data(self):
        pass

    def get_csv_header(self):
        pass
