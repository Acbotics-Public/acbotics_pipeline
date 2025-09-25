import icontract
import numpy as np
import copy
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_To_Float64(PR_Threaded_Process):
    """Converts a constant rate data container to be float64"""

    def handle_data(self, dc):
        """Convert data container to float64 and then send along"""
        dc = copy.deepcopy(dc)  # make a copy since we are modifying
        dc.data = dc.data.astype(np.float64)
        self.send_data(dc)
