from acbotics_pipeline.data_containers.data_container_sensor import (
    DataContainer_Sensor,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac


import threading
from time import sleep
import numpy as np


class Imu_To_Data_Container:
    def __init__(self, cpp_queue_imu=None):
        if cpp_queue_imu is None:
            cpp_queue_imu = ac.Q_IMU.create()
        self.cpp_queue_imu = cpp_queue_imu
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
        print("running imu_to_data thread")
        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_imu.size() > 0:
            data_frame_imu = self.cpp_queue_imu.pop()
            dic = {}
            dic["pitch_ned_deg"] = data_frame_imu.pitch_ned_deg
            dic["roll_ned_deg"] = data_frame_imu.roll_ned_deg
            dic["accel_x"] = data_frame_imu.accel_x
            dic["accel_y"] = data_frame_imu.accel_y
            dic["accel_z"] = data_frame_imu.accel_z
            dic["gyro_x"] = data_frame_imu.gyro_x
            dic["gyro_y"] = data_frame_imu.gyro_y
            dic["gyro_z"] = data_frame_imu.gyro_z
            data_frame = DataContainer_Sensor(
                timestamp=data_frame_imu.header.start_time_nsec,
                value_dict=dic,
                sensor_type="IMU",
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
