"""
Created on Apr 25, 2024

@author: sam
"""

import struct
from collections import namedtuple
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_sensor import DataContainer_Sensor
import numpy as np
import icontract

from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp


class Generic_Payload:
    def __init__(self, id1, id2):
        pass

    def decode(self, data, header):
        pass

    def encode_data(self, df):
        pass

    def get_sensor_type(self):
        return "UNK"

    def extract_times(self, value_dic):
        return None

    def get_raw_timestamp(self, timestamp):
        return timestamp.get_tick_time()

    def _get_sensor_timestamp(self, raw_timestamp):
        sensor_time = SensorTimestamp.from_tick(
            tick_time_int=raw_timestamp
        )  # TODO: Use Time ref?
        return sensor_time


class Sensor_Payload_GPS_2(Generic_Payload):
    def __init__(self, id1="G", id2="2", timestamp_src="UNIX"):
        super().__init__(id1=id1, id2=id2)
        self.id1 = id1
        self.id2 = id2
        self.timestamp_src = timestamp_src
        self.payload_fmt = "<ddHHHffffffffff"
        self.payload_Data = namedtuple(
            "payload_data",
            "lat lon sats mode status altHAE epx epy epd track speed eps eph climb epc",
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def get_sensor_type(self):
        return "GPS"

    def get_raw_timestamp(self, timestamp):
        """Overwrite since this is a  non ticked sensor"""
        return timestamp.get_wall_time()

    def _get_sensor_timestamp(self, raw_timestamp):
        """Overwrite since this is a  non ticked sensor"""
        sensor_time = SensorTimestamp.from_unix_time(
            unix_time_float=raw_timestamp
            * 1e9  # TODO: This is not nsec in current implementation
        )  # TODO: Use Time ref?
        return sensor_time

    def encode_data(self, df):
        payload = struct.pack(
            self.payload_fmt,
            df.value_dict["lat"],
            df.value_dict["lon"],
            int(df.value_dict["sats"]),
            int(df.value_dict["mode"]),
            int(df.value_dict["status"]),
            df.value_dict["altHAE"],
            df.value_dict["epx"],
            df.value_dict["epy"],
            df.value_dict["epd"],
            df.value_dict["track"],
            df.value_dict["speed"],
            df.value_dict["eps"],
            df.value_dict["eph"],
            df.value_dict["climb"],
            df.value_dict["epc"],
        )
        return payload

    def decode_data(self, data):
        value_dict = {}
        value_dict["lat"] = numpy.frombuffer(data, count=1, dtype=np.float64)[0]
        value_dict["lon"] = numpy.frombuffer(data, count=1, offset=8, dtype=np.float64)[
            0
        ]
        value_dict["sats"] = numpy.frombuffer(
            data, count=1, offset=16, dtype=np.uint16
        )[0]
        value_dict["mode"] = numpy.frombuffer(
            data, count=1, offset=18, dtype=np.uint16
        )[0]
        value_dict["status"] = numpy.frombuffer(
            data, count=1, offset=20, dtype=np.uint16
        )[0]
        value_dict["altHAE"] = numpy.frombuffer(
            data, count=1, offset=22, dtype=np.float32
        )[0]
        value_dict["epx"] = numpy.frombuffer(
            data, count=1, offset=26, dtype=np.float32
        )[0]
        value_dict["epy"] = numpy.frombuffer(
            data, count=1, offset=30, dtype=np.float32
        )[0]
        value_dict["epd"] = numpy.frombuffer(
            data, count=1, offset=34, dtype=np.float32
        )[0]
        value_dict["track"] = numpy.frombuffer(
            data, count=1, offset=38, dtype=np.float32
        )[0]
        value_dict["speed"] = numpy.frombuffer(
            data, count=1, offset=42, dtype=np.float32
        )[0]
        value_dict["eps"] = numpy.frombuffer(
            data, count=1, offset=46, dtype=np.float32
        )[0]
        value_dict["eph"] = numpy.frombuffer(
            data, count=1, offset=50, dtype=np.float32
        )[0]
        value_dict["climb"] = numpy.frombuffer(
            data, count=1, offset=54, dtype=np.float32
        )[0]
        value_dict["epc"] = numpy.frombuffer(
            data, count=1, offset=58, dtype=np.float32
        )[0]
        return value_dict


@icontract.require(lambda st: isinstance(st, str))
@icontract.require(lambda st: len(st) == 2)
def str_2_bytes(st):
    return (st[0].encode(), st[1].encode())


class PayloadMap:
    def __init__(self):
        self._default_payload_id_map = {}
        self._default_payload_name_map = {}
        self._default_payload_id_name_map = {}
        self._default_payload_name_id_map = {}
        self._add_payload(
            id=str_2_bytes("G2"), name="GPS", payload=Sensor_Payload_GPS_2()
        )

    def _add_payload(self, id, name, payload):
        self._default_payload_id_map[id] = payload
        self._default_payload_name_map[name] = payload
        self._default_payload_id_name_map[id] = name
        self._default_payload_name_id_map[name] = id

    def get_by_id(self, id):
        try:
            return self._default_payload_id_map[id]
        except KeyError:
            return None

    def get_id_by_name(self, name):
        try:
            return self._default_payload_id_map[name]
        except KeyError:
            return None


class UDP_Generic_Protocol:
    def __init__(self, time_filter=None):

        # notice we can't use "!" here due to packet formatting!
        self.header_fmt = "<QccH"
        self.Header_Data = namedtuple(
            "header_data",
            "TIMESTAMP ID1 ID2 NUM_BYTES",
        )
        self.time_filter = time_filter
        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

        self.payload_protocols = PayloadMap()

    def get_raw_timestamp(self, timestamp):
        return timestamp.get_tick_time() / 10

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        # eventually use version number to get proper format
        header = self.Header_Data._make(
            struct.unpack(self.header_fmt, data[0 : self.header_length_b])
        )
        return header

    def decode(self, data):
        header = self.decode_header(data)
        payload_parser = self.payload_protocols.get_by_id((header.ID1, header.ID2))
        if payload_parser is None:
            return None

        value_dict = payload_parser.decode_data(data[self.header_length_b :])
        sensor_timestamp = payload_parser._get_sensor_timestamp(header.TIMESTAMP)
        if self.time_filter is not None:
            self.time_filter.process_timestamp(sensor_timestamp)
        else:
            print("No time filter defined")
        return DataContainer_Sensor(
            timestamp=sensor_timestamp,
            value_dict=value_dict,
            sensor_type=payload_parser.get_sensor_type(),
            # timestamp_src=payload_parser.timestamp_src,
        )

    def encode_header(self, timestamp, id1, id2, num_bytes):
        header = struct.pack(
            self.header_fmt,
            int(timestamp),
            id1.encode(),
            id2.encode(),
            num_bytes,
        )
        return header

    def encode(self, df):
        sensor_type = df.sensor_type
        ids = self.payload_protocols.get_id_by_name(sensor_type)
        payload = self.payload_protocols.get_by_id(ids)
        ts = self.payload_protocols.get_raw_timestamp(df.timestamp)
        if ids is not None and payload is not None:
            header = self.encode_header(timestamp=ts, id1=ids[0], id2=ids[1])
            data = payload.encode_data()
            data_to_send = header + data
            return data_to_send
        return None
