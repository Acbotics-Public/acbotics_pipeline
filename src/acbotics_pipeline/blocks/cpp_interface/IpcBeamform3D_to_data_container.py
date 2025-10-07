from acbotics_pipeline.data_containers.data_container_beamformed_output_raw_simple import (
    DataContainer_Beamformed_Output_Raw_Simple,
)
from . import ac


import threading
from time import sleep
import numpy as np


class IpcBeamform3D_To_Data_Container:
    def __init__(self, cpp_queue_bf=None):
        if cpp_queue_bf is None:
            cpp_queue_bf = ac.Q_BF3D.create()
        self.cpp_queue_bf = cpp_queue_bf
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

        while True:
            self.run_once()
            sleep(0.1)

    def run_once(self):
        while self.cpp_queue_bf.size() > 0:
            data_frame_cpp = self.cpp_queue_bf.pop()
            beampattern = data_frame_cpp.viewBeamPattern()

            look_angle_vert = data_frame_cpp.viewLookAngleVertical()
            look_angle_bearings = data_frame_cpp.viewLookAngleBearings()
            beam_data = beampattern.reshape(
                (len(look_angle_bearings), len(look_angle_vert), beampattern.shape[1])
            )
            header = data_frame_cpp.header
            data_frame = DataContainer_Beamformed_Output_Raw_Simple(
                data=beam_data,
                thetas=look_angle_bearings,
                phis=look_angle_vert,
                frequencies=np.arange(beampattern.shape[1]),
                start_time=np.datetime64(header.start_time_nsec, "ns"),
            )
            for cb in self.callbacks:
                cb(data_frame)

    def process(self, t):
        pass
