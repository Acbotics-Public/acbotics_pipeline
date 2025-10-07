import icontract
import numpy as np
import queue
from collections import deque
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Buffer_Sensor(PR_Threaded_Process):
    def __init__(
        self,
        samples_to_keep,
    ):
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
        self.recreate_buffers()
        self.sample_rate = None
        super().__init__()

    def recreate_buffers(self):
        self.data_buffer = {"timestamp": deque(maxlen=self.samples_to_keep)}

    def is_waiting(self):
        return True

    def get_latest(self, signals=None):
        vals = {}
        if signals is None:
            signals = [k for k in self.data_buffer.keys()]
        for sig in signals:
            if len(self.data_buffer[sig]) == 0:
                continue
            if not sig in self.data_buffer.keys():
                continue
            vals[sig] = self.data_buffer[sig][-1]
        return vals

    def get_buffer(self, signals=None):
        x = self.data_buffer["timestamp"]
        ys = {}
        if signals is None:
            signals = [k for k in self.data_buffer.keys() if not k == "timestamp"]
        for sig in signals:
            if len(self.data_buffer[sig]) == 0:
                continue
            if not sig in self.data_buffer.keys():
                continue
            ys[sig] = np.array(self.data_buffer[sig])
        return (x, ys)

    def handle_data(self, dc):
        for k in dc.value_dict.keys():
            if not k in self.data_buffer.keys():
                self.data_buffer[k] = deque(
                    [0 for i in range(len(self.data_buffer["timestamp"]))],
                    maxlen=self.samples_to_keep,
                )
            self.data_buffer[k] += deque([dc.value_dict[k]])
        self.data_buffer["timestamp"] += deque([dc.timestamp])
