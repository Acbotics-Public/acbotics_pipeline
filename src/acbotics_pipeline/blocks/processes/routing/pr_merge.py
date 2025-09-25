import icontract
import numpy as np
import copy
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import queue


class Pr_Merge:
    """Take a number of separate data streams and combine them into a single stream with n channels.
    Assumes sample rates are equal. Assumes data times align (even if they are off by an integral
    number of samples."""

    def __init__(self, num_inputs):
        self.unprocessed_data = [queue.Queue() for i in range(num_inputs)]
        self.residual_data = [None for i in range(num_inputs)]
        self.callbacks = []
        self.num_inputs = num_inputs
        super().__init__()

    def get_number_of_input_channels(self):
        return self.num_inputs

    def get_number_of_output_channels(self):
        return 1

    def input_data(self, dc, channel):
        self.unprocessed_data[channel].put(copy.deepcopy(dc))

    def get_input_callback(self, channel):
        return lambda dc: self.input_data(dc, channel)

    def add_callback(self, function):
        self.callbacks.append(function)

    def _store_residual(self, dc, channel):
        if self.residual_data[channel] is None:
            print("Setting data channel since none")
            self.residual_data[channel] = dc
        else:
            previous_data = self.residual_data[channel]
            st_new = dc.get_start_time()
            et_old = previous_data.get_end_time() + np.timedelta64(
                int((1e9) / dc.get_sample_rate()), "ns"
            )
            if abs(st_new - et_old) > np.timedelta64(10, "ns"):
                print(
                    "Warning, times do not align: " + repr(st_new) + "!=" + repr(et_old)
                )
                print("Data index " + repr(dc.frame_count))
                print((st_new - et_old) / (1e9) * 8000)
                print(1e9 / dc.get_sample_rate())
                print(channel)
            self.residual_data[channel].add_data(dc.data)

    def is_waiting(self):
        return True

    def process(self, process_time):
        # how to combine?? Assume time synced for now
        # drive from first channel as "master"
        data = [[] for i in range(self.num_inputs)]
        while not self.unprocessed_data[0].empty():
            # handle channel 0. Pull just once since this is frame control
            dc = self.unprocessed_data[0].get()
            sample_rate = dc.get_sample_rate()

            self._store_residual(dc, 0)
            for i in range(1, self.num_inputs):
                # pull all data from remaining channels
                if not self.unprocessed_data[i].empty():
                    dc = self.unprocessed_data[i].get()
                    self._store_residual(dc, i)
            et = self.residual_data[0].get_end_time()
            st = self.residual_data[0].get_start_time()

            for i in range(0, self.num_inputs):
                et = min(et, self.residual_data[i].get_end_time())
                st = max(st, self.residual_data[i].get_start_time())
            for i in range(0, self.num_inputs):
                # remove any data in other channels from before this sample
                d = self.residual_data[i].pop_data_before(st)
            for i in range(self.num_inputs):
                data[i] = list(
                    self.residual_data[i].pop_data_before(
                        et + np.timedelta64(int(((1e9) / sample_rate) / 2), "ns")
                    )[0]
                )
            dc = DataContainer_Constant_Rate(
                data, sample_rate=sample_rate, start_time=st
            )

            for c in self.callbacks:
                c(dc)
