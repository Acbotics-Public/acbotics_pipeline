import icontract
import numpy as np

import copy

from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_Delay_Sample(PR_Threaded_Process):
    def __init__(self, delay_samples):
        self.delay = delay_samples
        super().__init__()

    def handle_data(self, dc):
        dc = copy.deepcopy(dc)
        dc.data = dc.data
        dc.start_time = dc.start_time + np.timedelta64(
            int(self.delay * ((1e9) / dc.get_sample_rate())), "ns"
        )
        self.send_data(dc)

    def process(self, process_time):
        pass
