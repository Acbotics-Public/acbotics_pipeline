import icontract
import numpy as np
import queue
from collections import deque
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Buffer_FFT(PR_Threaded_Process):
    def __init__(
        self,
        samples_to_keep,
    ):
        self.num_sigs = 1
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
        self.phone_sensitivity_db = -167.0
        self.recreate_buffers()
        self.sample_rate = -1
        self.paused = False
        super().__init__()

    def recreate_buffers(self):
        self.data_buffer = [
            deque(maxlen=self.samples_to_keep) for i in range(self.num_sigs)
        ]

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.recreate_buffers()

    def is_waiting(self):
        return True

    def get_buffer(self, chans=None):
        imgs = []
        for i in range(self.num_sigs):
            if len(self.data_buffer[i]) == 0:
                continue
            if chans is not None and not i in chans:
                continue
            imgs.append(np.array(self.data_buffer[i]).T)
        return imgs

    def get_sample_rate(self):
        return self.sample_rate

    def handle_data(self, dc):
        if self.paused:
            return
        data = dc.data
        sample_rate = dc.get_sample_rate()
        if not sample_rate == self.sample_rate:
            self.sample_rate = sample_rate
            # TODO: should this trigger a buffer reset?
        if not data.shape[0] == self.num_sigs:
            self.num_sigs = data.shape[0]
            self.recreate_buffers()
            print("number of channels changed. Reinit buffers")
        for i in range(self.num_sigs):
            self.data_buffer[i].append(
                20 * np.log10(np.abs(data[i, :])) - self.phone_sensitivity_db
            )
