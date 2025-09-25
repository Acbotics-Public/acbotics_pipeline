import icontract
import numpy as np
import struct
import copy

from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_Gain(PR_Threaded_Process):
    def __init__(self, gain):
        self.gain = gain
        super().__init__()

    def handle_data(self, dc):
        dc = copy.deepcopy(dc)
        dc.data = dc.data * self.gain
        self.send_data(dc)
