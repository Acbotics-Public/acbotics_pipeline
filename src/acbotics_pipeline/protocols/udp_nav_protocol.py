import struct
from collections import namedtuple
import copy
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_nav import DataContainer_Nav
import numpy as np


class UDP_Nav_Protocol:
    def __init__(self):
        self.VERSION_MAJOR_IND = 2
        self.VERSION_MINOR_IND = 3
        self.version_major = 0
        self.version_minor = 1
        self.header_fmt = "!BBBBqI"
        self.Header_Data = namedtuple(
            "header_data", "ID1 ID2 VER_MAJ VER_MIN START_TIME PACKET_NUM"
        )
        self.nav_fmt = "!dd?ddd?ddd?ddd?"
        self.nav_Data = namedtuple(
            "nav_data",
            "GPS_LAT GPS_LON GPS_VALID PITCH ROLL HEADING ORIENTATION_VALID VELOCITY_X VELOCITY_Y VELOCITY_Z VELOCITY_VALID ACCELERATION_X ACCELERATION_Y ACCELERATION_Z ACCELERATION_VALID",
        )

        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        if not data[0] == ord("A") or not data[1] == ord("N"):
            print("ignoring unrecognized packet header: " + repr(data[0:2]))
            return None
        # extract protocol version
        version_major = data[self.VERSION_MAJOR_IND]
        version_minor = data[self.VERSION_MINOR_IND]
        # eventually use version number to get proper format
        header = self.Header_Data._make(
            struct.unpack(self.header_fmt, data[0 : self.header_length_b])
        )
        return header

    def decode_data(self, data, header):
        data = self.nav_Data._make(
            struct.unpack(self.nav_fmt, data[self.header_length_b :])
        )
        return data

    def decode(self, data):
        header = self.decode_header(data)
        d = self.decode_data(data, header)
        dc = DataContainer_Nav(
            gps_lat=d.GPS_LAT,
            gps_lon=d.GPS_LON,
            gps_valid=d.GPS_VALID,
            pitch=d.PITCH,
            roll=d.ROLL,
            heading=d.HEADING,
            orientation_valid=d.ORIENTATION_VALID,
            velocity=np.array([d.VELOCITY_X, d.VELOCITY_Y, d.VELOCITY_Z]),
            velocity_valid=d.VELOCITY_VALID,
            acceleration=np.array(
                [d.ACCELERATION_X, d.ACCELERATION_Y, d.ACCELERATION_Z]
            ),
            acceleration_valid=d.ACCELERATION_VALID,
            start_time=np.datetime64(header.START_TIME, "ns"),
            frame_count=header.PACKET_NUM,
        )
        return dc

    def encode(self, dc, packet_number=None):
        if packet_number is None:
            packet_number = dc.frame_count

        frame_start_time = dc.get_start_time().astype(">i8")
        header = struct.pack(
            self.header_fmt,
            ord("A"),
            ord("N"),
            self.version_major,
            self.version_minor,
            frame_start_time,
            packet_number,
        )
        data = struct.pack(
            self.nav_fmt,
            dc.gps_lat,
            dc.gps_lon,
            dc.gps_valid,
            dc.pitch,
            dc.roll,
            dc.heading,
            dc.orientation_valid,
            dc.velocity[0],
            dc.velocity[1],
            dc.velocity[2],
            dc.velocity_valid,
            dc.acceleration[0],
            dc.acceleration[1],
            dc.acceleration[2],
            dc.acceleration_valid,
        )
        data_to_send = header + data
        return data_to_send
