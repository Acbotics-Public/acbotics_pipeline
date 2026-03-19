from acbotics_pipeline.data_containers.data_container_sensor import (
    DataContainer_Sensor,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac
from .generic_sensor_to_data_container import Generic_Sensor_To_Data_Container


import threading
from time import sleep
import numpy as np


class Bnr_To_Data_Container(Generic_Sensor_To_Data_Container):
    def __init__(self, cpp_queue_bnr=None, time_filter=None):
        super().__init__(time_filter)
        if cpp_queue_bnr is None:
            cpp_queue_bnr = ac.Q_BNR.create()
        self.cpp_queue_bnr = cpp_queue_bnr
        self.callbacks = []
        self.magnetic_callbacks = []
        self.acceleration_callbacks = []
        self.gyro_callbacks = []
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

    def add_acceleration_callback(self, function):
        self.acceleration_callbacks.append(function)

    def add_gyro_callback(self, function):
        self.gyro_callbacks.append(function)

    def add_magnetic_callback(self, function):
        self.magnetic_callbacks.append(function)

    def run_thread(self):
        print("running bnr_to_data thread")
        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_bnr.size() > 0:
            data_frame_bnr = self.cpp_queue_bnr.pop()
            dic = {}

            dic["status"] = data_frame_bnr.status
            dic["accuracy"] = data_frame_bnr.accuracy
            dic["quat_i"] = data_frame_bnr.quat_i
            dic["quat_j"] = data_frame_bnr.quat_j
            dic["quat_k"] = data_frame_bnr.quat_k
            dic["quat_r"] = data_frame_bnr.quat_r
            sensor_time = self._get_sensor_timestamp(data_frame_bnr.header)
            data_frame = DataContainer_Sensor(
                timestamp=sensor_time,
                value_dict=dic,
                sensor_type="BNR",
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
