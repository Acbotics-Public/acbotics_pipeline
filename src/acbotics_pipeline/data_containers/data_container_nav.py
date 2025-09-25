"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract
from .data_container import DataContainer
import numpy as np


class DataContainer_Nav(DataContainer):
    def __init__(
        self,
        gps_lat,
        gps_lon,
        gps_valid,
        pitch,
        roll,
        heading,
        orientation_valid,
        velocity,
        velocity_valid,
        acceleration,
        acceleration_valid,
        start_time,
        frame_count=None,
    ):
        self.gps_lat = gps_lat
        self.gps_lon = gps_lon
        self.gps_valid = gps_valid
        self.pitch = pitch
        self.roll = roll
        self.heading = heading
        self.orientation_valid = orientation_valid
        self.velocity = velocity
        self.velocity_valid = velocity_valid
        self.acceleration = acceleration
        self.acceleration_valid = acceleration_valid
        self.start_time = start_time
        self.frame_count = frame_count

    def is_constant_rate(self):
        return False

    def get_timestamps(self):
        return [self.start_time]

    @icontract.ensure(
        lambda result: isinstance(result, np.datetime64),
        "start_time must be datetime64",
    )
    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        """Returns the time of the last sample"""
        return self.start_time

    def __repr__(self):
        return """DataContainer_Nav:
        gps_lat: %f
        gps_lon: %f
        gps_valid: %d
        pitch: %f
        roll: %f
        heading: %f
        orientation_valid: %f
        velocity_x: %f
        velocity_y: %f
        velocity_z: %f
        velocity_valid: %d
        acceleration_x: %f
        acceleration_y: %f
        acceleration_z: %f
        acceleration_valid: %d
        time: %f
        frame_count: %d""" % (
            self.gps_lat,
            self.gps_lon,
            self.gps_valid,
            self.pitch,
            self.roll,
            self.heading,
            self.orientation_valid,
            self.velocity[0],
            self.velocity[1],
            self.velocity[2],
            self.velocity_valid,
            self.acceleration[0],
            self.acceleration[1],
            self.acceleration[2],
            self.acceleration_valid,
            self.start_time,
            self.frame_count,
        )
