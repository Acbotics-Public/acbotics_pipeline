import struct
from collections import namedtuple
import copy
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_nav import DataContainer_Nav
import numpy as np


class UDP_Saildrone_Nav_Protocol:
    def __init__(self):
        self.header_fmt = "!ccccIQ"
        self.Header_Data = namedtuple("header", "ID1 ID2 ENDIAN TYPE FRAME_NUM TIME")

        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        if not data[0] == ord("S") or not data[1] == ord("D"):
            print("ignoring unrecognized packet header: " + repr(data[0:2]))
            return None
        header = self.Header_Data._make(
            struct.unpack(self.header_fmt, data[0 : self.header_length_b])
        )
        return header

    def decode_data(self, data, header):
        data_raw = data[self.header_length_b :]
        nmea_str = data_raw.decode("utf-8")
        return nmea_str

    def decode(self, data):
        header = self.decode_header(data)
        nmea_str = self.decode_data(data, header)
        try:
            if header.TYPE == "1".encode("utf-8"):
                # GPGGA
                print("GPGGA")
                li = nmea_str.split("*")
                chksum_in = li[1]
                msg = li[0]
                li = msg.split(",")
                if not len(li) == 15:
                    print(
                        "Expected 15 fields. Received %d fileds in GPGGA message: "
                        % (len(li),)
                        + repr(msg)
                    )
                    return None
                if not li[0] == "$GPGGA":
                    print(
                        "Message type mismatch, Expected $GPGGA. Received: "
                        + repr(li[0])
                    )
                    return None
                t = float(li[1])
                lat = float(li[2][0:2]) + float(li[2][2:]) / 60
                latdir = li[3]
                if latdir == "S":
                    lat = -lat
                lon = float(li[4][0:3]) + float(li[4][3:]) / 60
                londir = li[5]
                if londir == "W":
                    lon = -lon
                quality = int(li[6])
                num_sats = int(li[7])
                dc = DataContainer_Nav(
                    gps_lat=lat,  # no gps in message
                    gps_lon=lon,
                    gps_valid=True,
                    pitch=0,
                    roll=0,
                    heading=0,
                    orientation_valid=False,
                    velocity=np.array([0, 0, 0]),
                    velocity_valid=False,
                    acceleration=np.array([0, 0, 0]),
                    acceleration_valid=False,
                    start_time=np.datetime64(
                        int(header.TIME * 1e6), "ns"
                    ),  # convert time from ms to ns
                    frame_count=header.FRAME_NUM,
                )
                return dc
            elif header.TYPE == "2".encode("utf-8"):
                # PCHRA
                li = nmea_str.split("*")
                chksum_in = li[1]
                msg = li[0]
                li = msg.split(",")
                if not len(li) == 6:
                    print(
                        "Expected 6 fields. Received %d fileds in $PCHRA message: "
                        % (len(li),)
                        + repr(msg)
                    )
                    return None
                if not li[0] == "$PCHRA":
                    print(
                        "Message type mismatch, Expected $PCHRA. Received: "
                        + repr(li[0])
                    )
                    return None
                t = float(li[1])
                roll = float(li[2])
                pitch = float(li[3])
                yaw = float(li[4])
                dc = DataContainer_Nav(
                    gps_lat=0,  # no gps in message
                    gps_lon=0,
                    gps_valid=False,
                    pitch=pitch,
                    roll=roll,
                    heading=yaw,
                    orientation_valid=True,
                    velocity=np.array([0, 0, 0]),
                    velocity_valid=False,
                    acceleration=np.array([0, 0, 0]),
                    acceleration_valid=False,
                    start_time=np.datetime64(
                        int(header.TIME * 1e6), "ns"
                    ),  # convert time from ms to ns
                    frame_count=header.FRAME_NUM,
                )
                return dc
        except Exception as e:
            print("Parse exception on message: " + repr(e))
            print(repr(header))
            print(nmea_str)
        return None

    def encode(self, dc, packet_number=None):
        if packet_number is None:
            packet_number = dc.frame_count

        frame_start_time = dc.get_start_time().astype(">i8")

        if dc.gps_valid:
            # GP
            msg_type = "1"
            msg = ""
        if dc.orientation_valid:
            msg_type = "2"  #
            msg - ""

        header = struct.pack(
            self.header_fmt,
            ord("S"),
            ord("D"),
            ord("<"),
            packet_number,
            frame_start_time,
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
