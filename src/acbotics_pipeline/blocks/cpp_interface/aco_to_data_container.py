from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac


import threading
from time import sleep
import numpy as np

from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp


class Aco_To_Data_Container:
    def __init__(self, cpp_queue_aco=None, time_filter=None):
        if cpp_queue_aco is None:
            cpp_queue_aco = ac.Q_ACO.create()
        self.cpp_queue_aco = cpp_queue_aco
        self.time_filter = time_filter
        self.callbacks = []
        self.thread = threading.Thread(target=self.run_thread)

        self.start()

    def start(self):
        self.stop = False
        self.thread.start()

    def is_waiting(self):
        return True

    def get_sample_rate(self):
        return self.sample_rate

    def add_callback(self, function):
        self.callbacks.append(function)

    # def cpp_callback(self, data_frame_cpp):
    #     data = data_frame_cpp.viewData()
    #     header = data_frame_cpp.header
    #     data_frame = DataContainer_Constant_Rate(
    #         data=data,
    #         sample_rate=header.sample_rate,
    #         start_time=np.datetime64(header.start_time_nsec, "ns"),
    #         start_count=header.adc_count,
    #         frame_count=header.packet_num,
    #     )
    #     for cb in self.callbacks:
    #         cb(data_frame)

    def run_thread(self):
        print("running aco_to_data thread")

        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_aco.size() > 0:
            data_frame_cpp = self.cpp_queue_aco.pop()
            data = data_frame_cpp.viewData()
            header = data_frame_cpp.header
            start_time = header.start_time_nsec
            sensor_time = SensorTimestamp.from_unix_time(
                unix_time_float=start_time
            )  # TODO: Find Time ref
            sensor_time.add_tick_time(
                tick_time_int=header.tick_time_nsec, state="PRIMARY"
            )
            if self.time_filter is not None:
                self.time_filter.process_timestamp(sensor_time)
            data_frame = DataContainer_Constant_Rate(
                data=data,
                sample_rate=header.sample_rate,
                start_time=sensor_time,
                start_count=header.adc_count,
                frame_count=header.packet_num,
                tick_time=header.tick_time_nsec,
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
