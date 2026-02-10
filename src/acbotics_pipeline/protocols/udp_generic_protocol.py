"""
Created on Apr 25, 2024

@author: oscar
"""

import struct
from collections import namedtuple
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_pt import DataContainer_PT
import numpy as np


class UDP_Generic_Protocol:
    def __init__(self):

        # notice we can't use "!" here due to packet formatting!
        self.header_fmt = "<QccH"
        self.Header_Data = namedtuple(
            "header_data",
            "TIMESTAMP ID1 ID2 NUM_BYTES",
        )
        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        # eventually use version number to get proper format
        header = self.Header_Data._make(
            struct.unpack(self.header_fmt, data[0 : self.header_length_b])
        )
        return header

    def decode_data(self, data, header):
        d = data[self.header_length_b :]

        data_array = None

        # unpack known generics
        if header.ID1 == b"P" and header.ID2 == b"T":
            pressure_mbar = numpy.frombuffer(d, count=1, dtype=np.uint32)[0] / 100
            temp_c = numpy.frombuffer(d, count=1, offset=4, dtype=np.int32)[0] / 100
            data_array = numpy.array([pressure_mbar, temp_c])

        return data_array

    def decode(self, data):
        header = self.decode_header(data)
        d = self.decode_data(data, header)

        dc = None
        if d is not None:
            if header.ID1 == b"P" and header.ID2 == b"T":
                dc = DataContainer_PT(
                    timestamp=np.datetime64(header.TIMESTAMP, "ns"),
                    pressure_mbar=d[0],
                    temp_c=d[1],
                )

        return dc

    def encode_header(self, timestamp, id1, id2, num_bytes):
        header = struct.pack(
            self.header_fmt,
            int(timestamp.iloc[0]),
            id1.encode(),
            id2.encode(),
            num_bytes,
        )
        return header
