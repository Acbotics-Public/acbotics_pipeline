import icontract
import numpy as np
import queue
from collections import deque
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Buffer_Beamform2D(PR_Threaded_Process):
    def __init__(
        self,
        samples_to_keep,
    ):
        self.num_sigs = 1
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
        # self.phone_sensitivity_db = -167.0
        self.recreate_buffers()
        super().__init__()

    def recreate_buffers(self):
        self.data_buffer = deque(maxlen=self.samples_to_keep)

    def is_waiting(self):
        return True

    def get_buffer(self):
        img = []
        if len(self.data_buffer) == 0:
            return img
        img = np.array(self.data_buffer.T)
        return img

    def handle_data(self, dc):
        data = dc.data
        thetas = dc.get_thetas()
        phis = dc.get_phis()
        # TODO: check/store thetas/phis to be queried later. Update if they change?
        self.data_buffer.append(data)
