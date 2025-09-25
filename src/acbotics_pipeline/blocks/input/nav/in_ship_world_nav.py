import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_nav import DataContainer_Nav
import math
import time


class In_Ship_World_Nav:
    def __init__(self, ship_name, world, output_rate):
        self.ship_name = ship_name
        self.world = world
        self.callbacks = []
        self.output_rate = output_rate
        self.count = 0
        self.last_message_time = None

    def is_waiting(self):
        return True

    def add_callback(self, function):
        self.callbacks.append(function)

    def process(self, process_time):
        if self.last_message_time is None:
            self.last_message_time = process_time

        if process_time - self.last_message_time > np.timedelta64(
            int(1e9 * 1 / self.output_rate), "ns"
        ):
            self.last_message_time = process_time
            ship = self.world.ships[self.ship_name]
            latlon = ship.get_latlon(process_time)
            if latlon is None:
                lat = 0
                lon = 0
                gps_val = False
            else:
                lat = latlon[0]
                lon = latlon[1]
                gps_val = True
            dc = DataContainer_Nav(
                gps_lat=lat,
                gps_lon=lon,
                gps_valid=gps_val,
                pitch=0,
                roll=0,
                heading=0,
                orientation_valid=False,
                velocity=[0, 0, 0],
                velocity_valid=False,
                acceleration=[0, 0, 0],
                acceleration_valid=False,
                start_time=process_time,
                frame_count=self.count,
            )
            self.count += 1
            for c in self.callbacks:
                c(dc)
