import struct
from collections import namedtuple
import copy
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import numpy as np


class UDP_Data_Protocol:
    def __init__(self):
        self.VERSION_MAJOR_IND = 2
        self.VERSION_MINOR_IND = 3
        self.version_major = 4
        self.version_minor = 1
        self.header_fmt = "!BBBBBBBIfqqIdI"
        self.Header_Data = namedtuple(
            "header_data",
            "ID1 ID2 VER_MAJ VER_MIN ENDIAN NUM_CHANNELS DATA_SIZE NUM_VALUES SAMPLE_RATE START_TIME TICK_TIME ADC_COUNT SCALE PACKET_NUM",
        )
        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        if not data[0] == ord("A") or not data[1] == ord("C"):
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
        d = data[self.header_length_b :]
        data_array = numpy.frombuffer(d, dtype=np.uint16).reshape(
            -1,
            header.NUM_CHANNELS,
        )
        #        if header.ENDIAN == ord('<'):
        #            data_array = data_array.byteswap()
        return data_array.transpose()

    def decode(self, data):
        header = self.decode_header(data)
        d = self.decode_data(data, header)
        dc = DataContainer_Constant_Rate(
            data=d,
            sample_rate=header.SAMPLE_RATE,
            start_time=np.datetime64(header.START_TIME, "ns"),
            frame_count=header.PACKET_NUM,
            start_count=0,
        )
        return dc

    def encode(
        self,
        data_array,
        sample_rate,
        start_time,
        scale,
        packet_number,
        force_endian=None,
        adc_count=0,
        tick_time=0,
    ):
        frame_start_time = start_time

        data_endian = data_array.dtype.byteorder
        if force_endian is not None:
            data_endian = force_endian
        elif data_endian == "=":  # system order:
            sys_endian = sys.byteorder
            if sys_endian == "little":
                data_endian = "<"
            else:
                data_endian = ">"

        header = struct.pack(
            self.header_fmt,
            ord("A"),
            ord("C"),
            self.version_major,
            self.version_minor,
            ord(data_endian),
            data_array.shape[0],
            data_array.dtype.itemsize * 8,
            data_array.size,
            sample_rate,
            frame_start_time,
            int(tick_time / 10),
            adc_count,  # adc count
            scale,
            packet_number,
        )
        data_to_send = header + data_array.transpose().tobytes()
        return data_to_send
