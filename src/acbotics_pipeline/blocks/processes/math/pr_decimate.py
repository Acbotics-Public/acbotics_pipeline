import icontract
import numpy as np
import copy
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
import scipy.signal
import queue
import math
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)


class Pr_Decimate(PR_Threaded_Process):
    def __init__(self, factor, min_output_block_size=1):
        self.unprocessed_data = np.array([])
        self.factor = factor
        self.min_output_block_size = min_output_block_size
        super().__init__()

    def handle_data(self, dc):
        (timestamps, data) = dc.get_timestamped_data()
        if self.unprocessed_data.size == 0:
            self.unprocessed_data = data
            self.times = timestamps
        else:
            self.unprocessed_data = np.append(self.unprocessed_data, data, 0)
            self.times.extend(timestamps)
        min_window_size = self.min_output_block_size * self.factor
        if self.unprocessed_data.shape[0] >= min_window_size:
            window_frames = math.floor(self.unprocessed_data.shape[0] / self.factor)
            window_size = window_frames * self.factor
            x = self.unprocessed_data[0:window_size, 0:]
            ts = self.times[0]
            self.unprocessed_data = self.unprocessed_data[window_size:]
            self.times = self.times[window_size:]
            # TODO If size of window not integral of downsampling factor, store residual?
            dc = DataContainer_Constant_Rate(
                data=x[:: self.factor, :].transpose(),
                sample_rate=dc.get_sample_rate() / self.factor,
                start_time=ts,
            )  # make a copy since we are modifying

            self.send_data(dc)
