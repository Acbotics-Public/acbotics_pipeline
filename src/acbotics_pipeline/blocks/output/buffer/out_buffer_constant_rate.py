import icontract
import numpy as np
import queue
from collections import deque
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
import threading


class CircularBuffer:
    def __init__(self, max_samples=100, num_channels=1, dtype=np.float64):
        self.max_samples = max_samples
        self.num_channels = num_channels
        self.dtype = dtype
        self.next_write_index = 0
        self.mutex = threading.Lock()
        self.reset_buffer()

    def reset_buffer(self):
        self.buffer = np.zeros((self.num_channels, self.max_samples), dtype=self.dtype)
        self.next_write_index = 0

    def add_data(self, data):
        (channels, samples) = data.shape
        if channels == self.num_channels:
            with self.mutex:
                if self.next_write_index + samples < self.max_samples:
                    # whole chunk fits without wrapping
                    self.buffer[
                        :, self.next_write_index : self.next_write_index + samples
                    ] = data
                    self.next_write_index += samples
                else:
                    remaining = self.max_samples - self.next_write_index
                    wrap = samples - remaining
                    self.buffer[
                        :, self.next_write_index : self.next_write_index + remaining
                    ] = data[:, 0:remaining]
                    self.buffer[:, 0:wrap] = data[:, remaining:samples]
                    self.next_write_index = wrap

    def get_buffer(self):
        (channels, samples) = self.buffer.shape
        ret = np.zeros(self.buffer.shape)
        with self.mutex:
            len_1 = samples - self.next_write_index
            len_2 = samples - len_1
            ret[:, 0:len_1] = self.buffer[
                :, self.next_write_index : self.next_write_index + len_1
            ]
            ret[:, len_1:] = self.buffer[:, 0:len_2]
        print(ret)
        return ret


class Out_Buffer_Constant_Rate(PR_Threaded_Process):
    def __init__(self, samples_to_keep, downsample=1):
        self.num_sigs = 1
        self.received_data = queue.Queue()
        self.samples_to_keep = samples_to_keep
        self.sample_rate = 10000
        self.downsample = downsample
        self.buffer_valid = False
        self.buffer_requested = True
        self.buffer_callback = None
        self.data_buffer = CircularBuffer(
            max_samples=self.samples_to_keep, num_channels=self.num_sigs
        )
        self.recreate_buffers()
        self.paused = False

        super().__init__()

    def recreate_buffers(self):
        self.data_buffer.num_channels = self.num_sigs
        self.data_buffer.reset_buffer()
        self.time_base = np.array(
            [x / self.sample_rate for x in range(0, self.samples_to_keep)]
        )

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.recreate_buffers()

    def is_waiting(self):
        return True

    def get_buffer(self, chans=None):
        # ys = []
        # for i in range(self.num_sigs):
        #     if len(self.data_buffer[i]) == 0:
        #         continue
        #     if chans is not None and not i in chans:
        #         continue
        #     if x is None:
        #         x = np.array(
        #             [x / self.sample_rate for x in range(0, len(self.data_buffer[i]))]
        #         )
        #     ys.append(np.array(self.data_buffer[i]))
        return (self.time_base, self.data_buffer.get_buffer())

    @icontract.require(lambda dc: dc.is_constant_rate(), "sample_rate must be constant")
    def handle_data(self, dc):
        if self.paused:
            return

        if not self.sample_rate == dc.get_sample_rate():
            self.sample_rate = dc.get_sample_rate()
            self.recreate_buffers()
        data = dc.data

        if not data.shape[0] == self.data_buffer.num_channels:
            self.num_sigs = data.shape[0]
            # self.data_buffer.num_channels = self.num_sigs
            self.recreate_buffers()
            print("number of channels changed. Reinit buffers")
        # total = data.shape[0, 1]
        # for i in range(self.num_sigs):
        #     d = data[i, :]
        #     if not self.downsample == 1:
        #         pass
        #     self.data_buffer[i] += deque(d)
        # if self.request_buffer and self.buffer_callback is not None:
        #     self.buffer_callback(self._get_buffer())
        #     self.request_buffer = False
        self.data_buffer.add_data(data)
