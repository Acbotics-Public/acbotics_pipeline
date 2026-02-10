from acbotics_pipeline.data_containers.data_container_sensor import (
    DataContainer_Sensor,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac


import threading
from time import sleep
import numpy as np


class Pts_To_Data_Container:
    def __init__(self, cpp_queue_pts=None):
        if cpp_queue_pts is None:
            cpp_queue_pts = ac.Q_PTS.create()
        self.cpp_queue_pts = cpp_queue_pts
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
        while self.cpp_queue_pts.size() > 0:
            data_frame_pts = self.cpp_queue_pts.pop()
            dic = {}
            dic["pressure_mbar"] = data_frame_pts.pressure_mbar
            dic["temperature_c"] = data_frame_pts.temperature_c
            data_frame = DataContainer_Sensor(
                timestamp=data_frame_pts.header.start_time_nsec,
                value_dict=dic,
                sensor_type="PTS",
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
