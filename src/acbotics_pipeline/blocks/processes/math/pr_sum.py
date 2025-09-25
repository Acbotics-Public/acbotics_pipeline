import icontract
import numpy as np
import copy
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_Sum(PR_Threaded_Process):
    def __init__(self):
        super().__init__()

    def get_number_of_input_channels(self):
        return 2

    def get_number_of_output_channels(self):
        return 1

    def handle_data(self, dc):
        dc = copy.deepcopy(dc)  # make a copy since we are modifying
        dc.data = np.sum(dc.data, 0)
        self.send_data(dc)
