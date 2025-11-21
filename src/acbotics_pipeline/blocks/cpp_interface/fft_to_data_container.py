from acbotics_pipeline.data_containers.data_container_fft import (
    DataContainer_FFT,
)
from . import ac


import threading
from time import sleep
import numpy as np


class FFT_To_Data_Container:
    def __init__(self, cpp_queue_fft=None):
        if cpp_queue_fft is None:
            cpp_queue_fft = ac.Q_FFT.create()
        self.cpp_queue_fft = cpp_queue_fft
        self.callbacks = []
        self.thread = threading.Thread(target=self.run_thread)

        self.start()

    def start(self):
        self.stop = False
        self.thread.start()

    def is_waiting(self):
        return True

    def add_callback(self, function):
        self.callbacks.append(function)

    def run_thread(self):
        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_fft.size() > 0:
            data_frame_cpp = self.cpp_queue_fft.pop()
            data = data_frame_cpp.viewData()
            header = data_frame_cpp.header
            sample_rate = data_frame_cpp.FS
            data_frame = DataContainer_FFT(
                data=data,
                start_time=np.datetime64(header.start_time_nsec, "ns"),
                sample_rate=sample_rate,
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
