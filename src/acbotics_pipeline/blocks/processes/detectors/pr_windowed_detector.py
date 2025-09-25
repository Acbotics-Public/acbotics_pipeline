import icontract
import numpy as np
import math
import copy
import abc
from abc import ABC, abstractmethod
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Pr_Windowed_Detector(PR_Threaded_Process):
    def __init__(self, window_width, pct_overlap):
        self.data = None
        self.window_width = int(window_width)
        self.pct_overlap = pct_overlap
        self.sample_rate = None
        super().__init__()

    def handle_data(self, data_to_process):
        if self.data is None:
            self.data = copy.deepcopy(data_to_process)
        else:
            self.data.add_data(data_to_process.data)
        while self.data.data.shape[1] >= self.window_width:
            d = self.data.data[: self.window_width]
            st = self.data.get_start_time()
            self.data.pop_data_before_index(
                math.floor(self.window_width * (100 - self.pct_overlap) / 100.0)
            )
            results = self.detect_on_window(
                data=d, start_time=st, sample_rate=self.data.get_sample_rate()
            )
            if results is not None:
                self.send_data(results)

    @abstractmethod
    def detect_on_window(self, data, start_time):
        pass

    def process(self, process_time):
        pass
