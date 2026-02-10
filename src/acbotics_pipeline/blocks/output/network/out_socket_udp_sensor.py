import icontract
import numpy as np
import time
from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP
from acbotics_pipeline.protocols.udp_generic_protocol import UDP_Generic_Protocol
from collections import namedtuple
import struct
import copy
import datetime


class Sensor_Payload_IMU(UDP_Generic_Protocol):
    def __init__(self, id1="I", id2="M"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.payload_fmt = "<ffhhhhhh"
        self.payload_Data = namedtuple(
            "payload_data",
            "pitch_ned_deg roll_ned_deg accel_x accel_y accel_z gyro_x gyro_y gyro_z SAMPLE_RATE START_TIME TICK_TIME ADC_COUNT SCALE PACKET_NUM",
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
        if not "pitch_ned_deg" in df.value_dict:
            pitch = 0
            roll = 0
        else:
            pitch = df.value_dict["pitch_ned_deg"]
            roll = df.value_dict["roll_ned_deg"]
        try:
            payload = struct.pack(
                self.payload_fmt,
                pitch,
                roll,
                int(df.value_dict["accel_x"]),
                int(df.value_dict["accel_y"]),
                int(df.value_dict["accel_z"]),
                int(df.value_dict["gyro_x"]),
                int(df.value_dict["gyro_y"]),
                int(df.value_dict["gyro_z"]),
            )
            return header + payload
        except:
            return None


class Sensor_Payload_PTS(UDP_Generic_Protocol):
    def __init__(self, id1="P", id2="T"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.pressure_mult = 100.0
        self.temperature_mult = 100.0

        self.payload_fmt = "<Ii"
        self.payload_Data = namedtuple("payload_data", "pressure_mbar temperature_c")
        self.payload_size = struct.calcsize(self.payload_fmt)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
        payload = struct.pack(
            self.payload_fmt,
            int(np.round(df.value_dict["pressure_mbar"] * self.pressure_mult)),
            int(np.round(df.value_dict["temperature_C"] * self.temperature_mult)),
        )
        return header + payload


class Sensor_Payload_RTC(UDP_Generic_Protocol):
    def __init__(self, id1="R", id2="T"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.payload_fmt = "<BBBBBBBB"
        self.payload_Data = namedtuple(
            "payload_data", "second minute hour dow day month year, blank"
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def val_to_bcd(self, val):
        return ((val // 10) << 4) + (val % 10)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
        tm = df.value_dict["rtc_time"]
        dt = datetime.datetime.fromtimestamp(tm)

        payload = struct.pack(
            self.payload_fmt,
            self.val_to_bcd(dt.second),
            self.val_to_bcd(dt.minute),
            self.val_to_bcd(dt.hour),
            self.val_to_bcd(dt.weekday()),
            self.val_to_bcd(dt.day),
            self.val_to_bcd(dt.month),
            self.val_to_bcd(dt.year - 2000),
            0,
        )
        return header + payload


class Sensor_Payload_BNO(UDP_Generic_Protocol):
    def __init__(self, id1="B", id2="N"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.sense_mult = 256
        self.payload_fmt = "<cBhhh"
        self.payload_Data = namedtuple(
            "payload_data", "sense_key status sense_x sense_y sense_z"
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
        try:
            payload = struct.pack(
                self.payload_fmt,
                df.value_dict["sense_type"].encode(),
                df.value_dict["status"],
                int(np.round(df.value_dict["sense_x"] * self.sense_mult)),
                int(np.round(df.value_dict["sense_y"] * self.sense_mult)),
                int(np.round(df.value_dict["sense_z"] * self.sense_mult)),
            )
            return header + payload
        except:
            return None


class Sensor_Payload_BNR(UDP_Generic_Protocol):
    def __init__(self, id1="B", id2="R"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.sense_mult = 256
        self.quat_mult = 1 << 14
        self.accuracy_mult = 1 << 12
        self.payload_fmt = "<Bhhhhh"
        self.payload_Data = namedtuple(
            "payload_data", "status quat_i quat_j quat_k quat_r accuracy"
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
        payload = struct.pack(
            self.payload_fmt,
            int(df.value_dict["status"]),
            int(np.round(df.value_dict["quat_i"] * self.quat_mult)),
            int(np.round(df.value_dict["quat_j"] * self.quat_mult)),
            int(np.round(df.value_dict["quat_k"] * self.quat_mult)),
            int(np.round(df.value_dict["quat_r"] * self.quat_mult)),
            int(np.round(df.value_dict["accuracy"] * self.accuracy_mult)),
        )
        return header + payload


class Sensor_Payload_EPT(UDP_Generic_Protocol):
    def __init__(self, id1="E", id2="P"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.pressure_mult = 10.0
        self.temperature_mult = 100.0
        self.payload_fmt = "<Ii"
        self.payload_Data = namedtuple(
            "payload_data", "pressure_mbar_x10 temperature_c_x100"
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
        payload = struct.pack(
            self.payload_fmt,
            int(np.round(df.value_dict["pressure_mbar"] * self.pressure_mult)),
            int(np.round(df.value_dict["temperature_C"] * self.temperature_mult)),
        )
        return header + payload


class Sensor_Payload_GPS_2(UDP_Generic_Protocol):
    def __init__(self, id1="G", id2="2"):
        super().__init__()
        self.id1 = id1
        self.id2 = id2
        self.payload_fmt = "<ddHHHffffffffff"
        self.payload_Data = namedtuple(
            "payload_data",
            "lat lon sats mode status altHAE epx epy epd track speed eps eph climb epc",
        )
        self.payload_size = struct.calcsize(self.payload_fmt)

    def encode(self, df):
        header = self.encode_header(
            timestamp=df.timestamp,
            id1=self.id1,
            id2=self.id2,
            num_bytes=self.payload_size,
        )
        print(df)
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
        return header + payload


default_sensor_mapping = {
    "IMU": Sensor_Payload_IMU(),
    "PTS": Sensor_Payload_PTS(),
    "EPT": Sensor_Payload_EPT(),
    "BNO": Sensor_Payload_BNO(),
    "RTC": Sensor_Payload_RTC(),
    "BNR": Sensor_Payload_BNR(),
    "GPS": Sensor_Payload_GPS_2(),
}


class Out_Socket_UDP_Sensor(Out_Socket_UDP):

    def __init__(self, sensor_dict=default_sensor_mapping, *args, **kwargs):
        self.sensor_dict = copy.copy(sensor_dict)
        super().__init__(*args, **kwargs)

    def get_protocol(self, sensor=None):
        """
        Returns the generic sensor protocol
        """
        if sensor is None:
            return UDP_Generic_Protocol()
        return self.sensor_dict[sensor]

    def handle_data(self, dc):
        """
        Method called when data is available from preceeding block
        """
        data_to_send = self.get_protocol(dc.sensor_type).encode(dc)
        if data_to_send is not None:
            self.socket.sendto(data_to_send, (self.ip_addr, self.port))
