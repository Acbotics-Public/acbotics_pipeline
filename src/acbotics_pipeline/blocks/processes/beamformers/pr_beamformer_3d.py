import icontract
import numpy as np
import struct
import copy
import math

from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)

import acbeamform
import time


class Pr_Beamformer_3D(Pr_Multiprocess_Process):
    def __init__(self, receiver, bf_config, sample_rate, window_size):
        self.receiver = receiver
        self.bf_config = bf_config
        self.sample_rate = sample_rate
        self.window_size = window_size
        super().__init__(as_process=True)

    def initialize_process(self):
        self.unprocessed_data = np.array([])
        self.times = []
        super().initialize_process()

    def handle_data(self, dc):
        print("handling beamform data")
        (timestamps, data) = dc.get_timestamped_data()
        if self.unprocessed_data.size == 0:
            self.unprocessed_data = data
            self.times = timestamps
        else:
            self.unprocessed_data = np.append(self.unprocessed_data, data, 0)
            self.times.extend(timestamps)
        if self.unprocessed_data.size == 0:
            return None
            print("No data to beamform on")
        if self.unprocessed_data.shape[0] > self.window_size:
            x = self.unprocessed_data[0 : self.window_size, 0:]
            # use time at center of window
            ts = self.times[int(self.window_size / 2)]
            new_start = math.floor(self.window_size)
            self.unprocessed_data = self.unprocessed_data[self.window_size :]
            self.times = self.times[new_start:]
            print("Calculating beamform")
            [thetas, phis, B_out] = acbeamform.process_data_beamform_faster(
                receiver=self.receiver,
                bf_config=self.bf_config,
                windowed_data=x,
                data_time=ts,
            )
            print("Calc completed. Sending beamform.")
            dc = DataContainer_Beamformed_Output_2D(
                data=B_out, thetas=thetas, phis=phis, start_time=ts
            )

            print("Beamform calculated")
            return dc
        print("Waiting for Window to fill in beamformer")
        return None
