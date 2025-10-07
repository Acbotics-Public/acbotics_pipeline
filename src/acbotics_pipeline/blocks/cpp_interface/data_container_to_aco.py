from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
import threading
from time import sleep
import numpy as np
import queue

from . import ac


class Data_Container_To_ACO(PR_Threaded_Process):
    def __init__(self, cpp_queue_aco):
        self.cpp_queue_aco = cpp_queue_aco
        super().__init__()

    def start(self):
        self.stop = False
        self.thread.start()

    def handle_data(self, data_frame):
        self.dataframes.put(data_frame)

    def is_waiting(self):
        return True

    def get_sample_rate(self):
        return self.sample_rate

    def add_callback(self, function):
        self.callbacks.append(function)

    def run_thread(self):
        print("running aco thread")

        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while True:
            try:
                data_frame = self.dataframes.get_nowait()
                num_channels, num_values = data_frame.data.shape
                data_frame_cpp = ac.UdpAcousticData.create(
                    data_frame.data,
                    num_channels,
                    num_values,
                    data_frame.sample_rate,
                    data_frame.start_time,
                    data_frame.tick_time,
                    data_frame.start_count,
                    data_frame.frame_count,
                )
                self.cpp_queue_aco.push(data_frame_cpp)
            except queue.Empty:
                break

    def process(self, t):
        pass
