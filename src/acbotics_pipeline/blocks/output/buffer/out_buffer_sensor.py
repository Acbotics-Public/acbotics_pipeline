import icontract
import numpy as np
import queue
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process

import numbers
import threading


class Out_Buffer_Sensor(PR_Threaded_Process):
    def __init__(
        self,
        samples_to_keep,
    ):
        self.channels = {"timestamp": np.uint64}
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
        self.recreate_buffers()
        self.sample_rate = None
        self.paused = False
        self.next_write_index = 0
        self.mutex = threading.Lock()
        self.filled = False
        super().__init__()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.recreate_buffers()

    def recreate_buffers(self):
        self.data_buffer = {}
        for k, v in self.channels.items():
            self.data_buffer[k] = np.zeros(self.samples_to_keep, dtype=v)
        self.next_write_index = 0
        self.filled = False

    def is_waiting(self):
        return True

    def get_signal_names(self):
        return list(self.data_buffer.keys())

    def get_latest(self, signals=None):
        vals = {}
        if signals is None:
            signals = self.get_signal_names()
        for sig in signals:
            if not sig in self.data_buffer.keys():
                continue
            vals[sig] = self.data_buffer[sig][self.next_write_index - 1]
        return vals

    def get_buffer(self, signals=None):
        ys = {}
        with self.mutex:
            if self.filled:
                x = np.zeros(self.samples_to_keep)
            else:
                x = np.zeros(self.next_write_index - 1)

            # x = np.array(self.data_buffer["timestamp"])
            if self.filled:
                len_1 = self.samples_to_keep - self.next_write_index
                x[0:len_1] = self.data_buffer["timestamp"][self.next_write_index :]
                x[len_1:] = self.data_buffer["timestamp"][0 : self.next_write_index]
            else:
                x[0 : self.next_write_index - 1] = self.data_buffer["timestamp"][
                    0 : self.next_write_index - 1
                ]
            if signals is None:
                signals = [k for k in self.data_buffer.keys() if not k == "timestamp"]
            for sig in signals:
                if len(self.data_buffer[sig]) == 0:
                    continue
                if not sig in self.data_buffer.keys():
                    continue
                if self.filled:
                    ys[sig] = np.zeros(self.samples_to_keep)
                    ys[sig][0:len_1] = self.data_buffer[sig][self.next_write_index :]
                    ys[sig][len_1:] = self.data_buffer[sig][0 : self.next_write_index]
                else:
                    ys[sig] = np.zeros(self.next_write_index - 1)
                    ys[sig][0 : self.next_write_index - 1] = self.data_buffer[sig][
                        0 : self.next_write_index - 1
                    ]

        return (x, ys)

    def handle_data(self, dc):
        if self.paused:
            return
        new_channels = False
        for k in dc.value_dict.keys():
            if not k in self.data_buffer.keys():
                dtype = np.float64
                if isinstance(dc.value_dict[k], numbers.Integral):
                    dtype = np.int64
                elif isinstance(dc.value_dict[k], float):
                    dtype = np.float64
                # elif isinstance(dc.value_dict[k], str)
                #     dtype =np.str
                self.channels[k] = dtype
                new_channels = True
        with self.mutex:
            if new_channels:
                self.recreate_buffers()

            for k in dc.value_dict.keys():
                self.data_buffer[k][self.next_write_index] = dc.value_dict[k]
            self.data_buffer["timestamp"][
                self.next_write_index
            ] = dc.timestamp.get_tick_time()

            self.next_write_index = (self.next_write_index + 1) % self.samples_to_keep
            if self.next_write_index == 0:
                self.filled = True
