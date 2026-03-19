import copy
import icontract
from .data_container import DataContainer
import numpy as np

import acbotics_pipeline.helpers.contract_helpers as ch
from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp


class DataContainer_Sensor(DataContainer):
    @ch.argtype("timestamp", SensorTimestamp)
    @ch.argtype("sensor_type", str)
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
        out = []
        for k in sorted(self.value_dict.keys()):
            out.append(self.value_dict[k])
        return ([self.timestamp], np.array(out))

    def get_csv_header(self):
        return [k for k in sorted(self.value_dict.keys())]
