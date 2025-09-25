from abc import ABC, abstractmethod
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import math


class In_Square(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    @icontract.require(
        lambda duty_cycle: duty_cycle >= 0, "Duty Cycle must be positive"
    )
    @icontract.require(lambda duty_cycle: duty_cycle <= 1, "Duty Cycle cannot exceed 1")
    def __init__(
        self,
        frequency,
        amplitude,
        sample_rate,
        start_time,
        duty_cycle=0.5,
        output_batch_size=1,
    ):
        self.sample_rate = sample_rate
        self.frequency = frequency
        self.amplitude = amplitude
        self.output_batch_size = output_batch_size
        self.callbacks = []
        self.last_sent_index = 0
        self.start_time = start_time
        self.output_start_time = start_time  # should this be in a start function
        self.data_buffer = []
        self.next_sample_time = self.start_time
        self.samples_given = 0
        self.duty_cycle = duty_cycle

    def is_waiting(self):
        return True

    def get_sample_rate(self):
        return self.sample_rate

    def add_callback(self, function):
        self.callbacks.append(function)

    def process(self, process_time):
        t_start = (self.next_sample_time - self.start_time) / np.timedelta64(1, "s")
        t_stop = (process_time - self.start_time) / np.timedelta64(1, "s")
        t = np.arange(t_start, t_stop, step=1 / self.sample_rate)
        period = 1 / self.frequency
        t_diff = t % period

        x = self.amplitude * (t_diff < period * self.duty_cycle)
        self.next_sample_time = self.next_sample_time + np.timedelta64(
            int(1e9 * len(t) / self.sample_rate), "ns"
        )
        self.data_buffer.extend(x)
        while len(self.data_buffer) >= self.output_batch_size:
            output_data = self.data_buffer[: self.output_batch_size]
            self.data_buffer = self.data_buffer[self.output_batch_size :]
            dc = DataContainer_Constant_Rate(
                data=output_data,
                sample_rate=self.sample_rate,
                start_time=self.start_time
                + np.timedelta64(
                    int(1e9 * self.samples_given / self.sample_rate), "ns"
                ),
                frame_count=self.samples_given,
            )
            self.samples_given += len(output_data)
            for c in self.callbacks:
                c(dc)
