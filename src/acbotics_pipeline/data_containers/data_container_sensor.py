import copy
import icontract
from .data_container import DataContainer
import numpy as np


class DataContainer_Sensor(DataContainer):
    def __init__(self, timestamp, value_dict, sensor_type="UNK"):
        self.timestamp = timestamp
        self.value_dict = copy.copy(value_dict)
        self.sensor_type = sensor_type

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
        retval = """DataContainer_Sensor:
        time: %f\r\n""" % (
            self.timestamp,
        )

        for k in sorted(self.value_dict.keys()):
            retval += "  " + repr(k) + ":" + repr(self.value_dict[k]) + "\r\n"
        return retval

    def get_timestamped_data(self):
        return ([self.timestamp], np.array([[self.pressure_mbar, self.temp_c]]))

    def get_csv_header(self):
        return [k for k in sorted(self.value_dict.keys())]
