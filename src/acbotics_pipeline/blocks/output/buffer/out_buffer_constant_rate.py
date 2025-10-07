import icontract
import numpy as np
import queue
from collections import deque
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Buffer_Constant_Rate(PR_Threaded_Process):
    def __init__(
        self,
        samples_to_keep,
    ):
        self.num_sigs = 1
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
        self.recreate_buffers()
        self.sample_rate = None
        super().__init__()

    def recreate_buffers(self):
        self.data_buffer = [
            deque(maxlen=self.samples_to_keep) for i in range(self.num_sigs)
        ]

    def is_waiting(self):
        return True

    def get_buffer(self, chans=None):
        x = None
        ys = []
        for i in range(self.num_sigs):
            if len(self.data_buffer[i]) == 0:
                continue
            if chans is not None and not i in chans:
                continue
            if x is None:
                x = np.array(
                    [x / self.sample_rate for x in range(0, len(self.data_buffer[i]))]
                )
            ys.append(np.array(self.data_buffer[i]))
        return (x, ys)

    @icontract.require(lambda dc: dc.is_constant_rate(), "sample_rate must be constant")
    def handle_data(self, dc):
        self.sample_rate = dc.get_sample_rate()
        data = dc.data
        if not data.shape[0] == self.num_sigs:
            self.num_sigs = data.shape[0]
            self.recreate_buffers()
            print("number of channels changed. Reinit buffers")
        for i in range(self.num_sigs):
            self.data_buffer[i] += deque(data[i, :])
