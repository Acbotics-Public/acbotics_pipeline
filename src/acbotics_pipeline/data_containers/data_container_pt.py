"""
Created on Apr 25, 2024

@author: oscar
"""

import icontract
from .data_container import DataContainer
import numpy as np


class DataContainer_PT(DataContainer):
    def __init__(
        self,
        timestamp,
        pressure_mbar,
        temp_c,
    ):
        self.timestamp = timestamp
        self.pressure_mbar = pressure_mbar
        self.temp_c = temp_c

    def is_constant_rate(self):
        return False

    def get_timestamps(self):
        return [self.timestamp]

    @icontract.ensure(
        lambda result: isinstance(result, np.datetime64),
        "start_time must be datetime64",
    )
    def get_start_time(self):
        return self.timestamp

    def get_end_time(self):
        """Returns the time of the last sample"""
        return self.timestamp

    def __repr__(self):
        # pprint(self.__dict__, indent=2)
        return """DataContainer_PT:
        time: %f
        pressure: %f mbar
        temperature: %d C
        """ % (
            self.timestamp,
            self.pressure_mbar,
            self.temp_c,
        )

    def get_timestamped_data(self):
        return ([self.timestamp], np.array([[self.pressure_mbar, self.temp_c]]))

    def get_csv_header(self):
        return ["pressure_mbar", "temp_c"]
