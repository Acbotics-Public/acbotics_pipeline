import icontract
import numpy as np
import copy
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_Add_Constant(PR_Threaded_Process):
    def __init__(self, val):
        self.val = val
        super().__init__()

    def handle_data(self, dc):
        dc = copy.deepcopy(dc)  # make a copy since we are modifying
        dc.data = dc.data + self.val
        self.send_data(dc)
