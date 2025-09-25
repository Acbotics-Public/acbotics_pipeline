import icontract
import numpy as np
import struct
import copy

from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_Noise_Gaussian(PR_Threaded_Process):
    def __init__(self, scale):
        self.scale = scale
        super().__init__()

    def handle_data(self, dc):
        dc = copy.deepcopy(dc)
        dc.data = dc.data + np.random.normal(0, self.scale, dc.data.shape)
        self.send_data(dc)
