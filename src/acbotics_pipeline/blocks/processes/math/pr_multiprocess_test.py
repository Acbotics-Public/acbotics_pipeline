import icontract
import numpy as np
import struct
import copy

from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)


class Pr_Multiprocess_Test(Pr_Multiprocess_Process):
    def __init__(self, gain):
        self.gain = gain
        super().__init__()

    def handle_data(self, dc):
        dc = copy.deepcopy(dc)
        dc.data = dc.data * self.gain
        return dc
