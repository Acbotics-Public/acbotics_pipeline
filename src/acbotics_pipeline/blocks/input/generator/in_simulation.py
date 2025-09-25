import acsimarray

import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import math
import time
import copy


class In_Simulation:
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(self, receiver_name, world, model, start_time, output_batch_size=1000):
        self.receiver_name = receiver_name
        self.world = world
        self.output_batch_size = output_batch_size
        self.callbacks = []
        self.start_time = start_time
        self.data_buffer = []
        self.next_sample_time = self.start_time
        self.model = model
        self.stopped = False

    def is_waiting(self):
        return True

    def stop(self):
        self.stopped = True

    def get_sample_rate(self):
        return self.world.receivers[self.receiver_name].array_config["sample_rate"]

    def add_callback(self, function):
        self.callbacks.append(function)

    def process(self, process_time):
        if self.stopped:
            return
        st = time.process_time()
        receiver = self.world.receivers[self.receiver_name]
        win_length = receiver.array_config["window_length_s"] * self.get_sample_rate()
        if (process_time - self.next_sample_time) / np.timedelta64(
            1, "s"
        ) < win_length / self.get_sample_rate():
            return
        data = np.zeros((win_length, receiver.array_config["num_elements"]))
        ship_copy = copy.copy(self.world.ships)  # copy to avoid insertions during loop
        for ship_name, ship in ship_copy.items():
            if ship.active(self.next_sample_time):
                # print(ship_name)

                # TODO: Add receiver location to calls for array not at origin
                v = acsimarray.sim_ship_data_window(
                    receiver, ship, self.next_sample_time
                )
                # print(np.max(v))
                data += v
        pinger_copy = copy.copy(self.world.pingers)
        for pinger_name, pinger in pinger_copy.items():
            if pinger.active(self.next_sample_time):
                # print(pinger_name)
                v = self.model.run_model(receiver, pinger, self.next_sample_time)
                data += v

        dc = DataContainer_Constant_Rate(
            data=data.transpose(),
            sample_rate=self.get_sample_rate(),
            start_time=self.next_sample_time,
            frame_count=0,
        )
        last_sample_time = self.next_sample_time
        self.next_sample_time = self.next_sample_time + np.timedelta64(
            int(win_length / self.get_sample_rate()), "s"
        )
        print("Time delta: " + repr(self.next_sample_time - last_sample_time))
        for c in self.callbacks:
            c(dc)
        # print("In ship noise time = " + repr(time.process_time()-st))
