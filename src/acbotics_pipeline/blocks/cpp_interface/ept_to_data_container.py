from acbotics_pipeline.data_containers.data_container_sensor import (
    DataContainer_Sensor,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac


import threading
from time import sleep
import numpy as np


class Ept_To_Data_Container:
    def __init__(self, cpp_queue_ept=None):
        if cpp_queue_ept is None:
            cpp_queue_ept = ac.Q_EPT.create()
        self.cpp_queue_ept = cpp_queue_ept
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

    def run_thread(self):
        print("running pts_to_data thread")
        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_ept.size() > 0:
            data_frame_ept = self.cpp_queue_ept.pop()
            dic = {}
            dic["pressure_mbar"] = data_frame_ept.pressure_mbar
            dic["temperature_c"] = data_frame_ept.temperature_c
            data_frame = DataContainer_Sensor(
                timestamp=data_frame_ept.header.start_time_nsec,
                value_dict=dic,
                sensor_type="EPT",
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
