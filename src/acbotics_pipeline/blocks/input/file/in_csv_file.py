from abc import ABC, abstractmethod
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)

import csv


class In_CSV_File(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(self, filename, start_time, output_batch_size=1):
        self.chunk_size = 50
        self.channels = 8
        self.callbacks = []
        self.csv_file = open(
            filename,
        )
        self.reader = csv.reader(self.csv_file)

        self.last_sent_index = 0
        self.start_time = start_time

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return 1

    def get_sample_rate(self):
        return 52734

    def add_callback(self, function):
        self.callbacks.append(function)

    def is_waiting(self):
        return True

    def process(self, process_time):
        data = np.zeros((self.channels, self.chunk_size), np.int16)
        t = 0
        tick = 0

        for i in range(self.chunk_size):
            try:
                row = self.reader.__next__()
                if i == 0:
                    t = row[0]
                    tick = row[1]
                data[:, i] = row[2:]
            except StopIteration:
                return

        dc = DataContainer_Constant_Rate(
            data=data,
            sample_rate=self.get_sample_rate(),
            start_time=t,
            start_count=0,
        )
        # TODO, fix to update start time by how far first sample is in.

        for c in self.callbacks:
            c(dc)
