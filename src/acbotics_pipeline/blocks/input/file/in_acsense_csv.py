from abc import ABC, abstractmethod
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)


import datetime
import csv


class In_AcSense_CSV_File(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(
        self,
        filename,
        # start_time,
        output_batch_size=1,
        use_csv_time=True,
        rate=1.0,
        sample_rate=52734,
    ):
        self.chunk_size = 50
        self.use_csv_time = use_csv_time
        self.rate = 1.0
        self.sample_rate = sample_rate
        self.callbacks = []
        self.csv_file = open(
            filename,
        )
        self.reader = csv.reader(self.csv_file)
        self.header = next(self.reader)
        self.tick_index = -1
        self.ts_index = -1
        self.adc_count_index = -1
        self.packet_num_index = -1
        self.chan_start_index = -1
        self.num_channels = -1
        if "epoch_nsec" in self.header:
            self.ts_index = self.header.index("epoch_nsec")
        if "tick_time_nsec" in self.header:
            self.tick_index = self.header.index("tick_time_nsec")
        if "adc_count" in self.header:
            self.adc_count_index = self.header.index("adc_count")
        if "packet_num" in self.header:
            self.packet_num_index = self.header.index("packet_num")
        if "0" in self.header:
            self.chan_start_index = self.header.index("0")
            self.num_channels = 1
        if self.chan_start_index >= 0:
            for i in range(self.chan_start_index + 1, len(self.header)):
                try:
                    ind = int(self.header[i])
                    if ind == self.num_channels:
                        self.num_channels += 1
                    else:
                        break
                except ValueError:
                    break

        self.last_sent_index = 0
        # self.start_time = start_time

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return self.num_channels

    def get_sample_rate(self):
        return self.sample_rate

    def add_callback(self, function):
        self.callbacks.append(function)

    def is_waiting(self):
        return True

    def process(self):
        pass

    def run(self):
        self.start_time = datetime.datetime.now()

    def run_once(self):
        data = np.zeros((self.num_channels, self.chunk_size), np.int16)
        t = 0
        tick = 0
        packet_num = 0
        adc_count = 0

        for i in range(self.chunk_size):
            try:
                row = self.reader.__next__()
                if i == 0:
                    t = row[self.ts_index]
                    if self.tick_index >= 0:
                        tick = row[self.tick_index]
                    if self.adc_count_index >= 0:
                        adc_count = row[self.adc_count_index]
                    if self.packet_num_index >= 0:
                        packet_num = row[self.packet_num_index]
                data[:, i] = row[
                    self.chan_start_index : self.chan_start_index + self.num_channels
                ]

            except StopIteration:
                return

        dc = DataContainer_Constant_Rate(
            data=data,
            sample_rate=self.get_sample_rate(),
            start_time=t,
            start_count=adc_count,
            frame_count=packet_num,
            tick_time=tick,
        )

        for c in self.callbacks:
            c(dc)
