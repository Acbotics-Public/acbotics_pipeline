import icontract
import numpy as np
import struct
import copy
import math

import arlpy.bf

from acbotics_pipeline.data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)


class Pr_Beamformer_Bartlett:
    def __init__(
        self,
        positions,
        frequency,
        angles,
        window_size,
        overlap_pct,
        speed_of_sound=1500,
    ):
        self.unprocessed_data = np.array([])
        self.times = []
        self.num_inputs = len(positions)
        self.window_size = window_size
        self.overlap_pct = overlap_pct
        self.angles = angles
        self.steering = arlpy.bf.steering_plane_wave(
            pos=positions, c=speed_of_sound, theta=angles
        )
        self.frequency = frequency
        self.callbacks = []

    def get_number_of_input_channels(self):
        return 1

    def get_number_of_output_channels(self):
        return 1

    def is_waiting(self):
        return True

    def input_data(self, dc):
        (timestamps, data) = dc.get_timestamped_data()
        if self.unprocessed_data.size == 0:
            self.unprocessed_data = data
            self.times = timestamps
        else:
            self.unprocessed_data = np.append(self.unprocessed_data, data, 0)
            self.times.extend(timestamps)

    def add_callback(self, function):
        self.callbacks.append(function)

    def process(self, process_time):
        if self.unprocessed_data.size == 0:
            return
        if self.unprocessed_data.shape[0] > self.window_size:
            x = self.unprocessed_data[0:, 0 : self.window_size].transpose()
            ts = self.times[int(self.window_size / 2)]
            new_start = math.floor(self.window_size * self.overlap_pct / 100.0)
            self.unprocessed_data = self.unprocessed_data[new_start:]
            self.times = self.times[new_start:]
            y = arlpy.bf.bartlett(x, self.frequency, self.steering)
            dc = DataContainer_Beamformed_Output_1d(
                data=y, angles=self.angles, start_time=ts
            )
            for c in self.callbacks:
                c(dc)
