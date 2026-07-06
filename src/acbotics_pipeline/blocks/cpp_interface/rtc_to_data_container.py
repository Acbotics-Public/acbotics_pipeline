from acbotics_pipeline.data_containers.data_container_sensor import (
    DataContainer_Sensor,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac
from .generic_sensor_to_data_container import Generic_Sensor_To_Data_Container


import threading
from time import sleep
import numpy as np


class Rtc_To_Data_Container(Generic_Sensor_To_Data_Container):
    def __init__(self, cpp_queue_rtc=None, time_filter=None):
        super().__init__(time_filter)
        if cpp_queue_rtc is None:
            cpp_queue_rtc = ac.Q_RTC.create()
        self.cpp_queue_rtc = cpp_queue_rtc
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
        while self.cpp_queue_rtc.size() > 0:
            data_frame_rtc = self.cpp_queue_rtc.pop()
            dic = {}
            dic["rtc_time"] = data_frame_rtc.rtc_time
            sensor_time = self._get_sensor_timestamp(data_frame_rtc.header)
            data_frame = DataContainer_Sensor(
                timestamp=sensor_time,
                value_dict=dic,
                sensor_type="RTC",
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
