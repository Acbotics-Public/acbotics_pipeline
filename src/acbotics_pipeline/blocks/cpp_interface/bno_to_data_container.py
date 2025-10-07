from acbotics_pipeline.data_containers.data_container_sensor import (
    DataContainer_Sensor,
)
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from . import ac


import threading
from time import sleep
import numpy as np


class Bno_To_Data_Container:
    def __init__(self, cpp_queue_bno=None):
        if cpp_queue_bno is None:
            cpp_queue_bno = ac.Q_BNO.create()
        self.cpp_queue_bno = cpp_queue_bno
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
        print("running bno_to_data thread")
        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_bno.size() > 0:
            data_frame_bno = self.cpp_queue_bno.pop()
            dic = {}
            sense_type = data_frame_bno.sense_type

            dic["sense_type"] = data_frame_bno.sense_type
            dic["status"] = data_frame_bno.status
            dic["sense_x"] = data_frame_bno.sense_x
            dic["sense_y"] = data_frame_bno.sense_y
            dic["sense_z"] = data_frame_bno.sense_z
            data_frame = DataContainer_Sensor(
                timestamp=data_frame_bno.header.start_time_nsec, value_dict=dic
            )
            for cb in self.callbacks:
                cb(data_frame)

            if sense_type == ac.BNO_TYPE.ACCEL:
                for cb in self.acceleration_callbacks:
                    cb(data_frame)

            if sense_type == ac.BNO_TYPE.GYRO:
                for cb in self.gyro_callbacks:
                    cb(data_frame)

            if sense_type == ac.BNO_TYPE.MAG:
                for cb in self.magnetic_callbacks:
                    cb(data_frame)

    def process(self, t):
        pass
