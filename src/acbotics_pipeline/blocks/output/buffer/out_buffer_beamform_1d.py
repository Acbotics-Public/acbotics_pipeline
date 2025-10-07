import icontract
import numpy as np
import queue
from collections import deque
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Buffer_Beamform1D(PR_Threaded_Process):
    def __init__(
        self,
        samples_to_keep,
    ):
        self.num_sigs = 1
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
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
        img = np.array(self.data_buffer)
        return img

    def handle_data(self, dc):
        data = dc.data
        angles = dc.get_angles()
        # TODO: check/store angles to be queried later. Update if they change?
        data_norm = data - np.min(data, axis=0)
        data_norm = data / np.max(data, axis=0)

        self.data_buffer.append(data_norm)
