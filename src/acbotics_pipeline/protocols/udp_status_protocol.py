import struct
from collections import namedtuple
import copy
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_status import DataContainer_Status
import numpy as np


class UDP_Status_Protocol:
    def __init__(self):
        self.VERSION_MAJOR_IND = 2
        self.VERSION_MINOR_IND = 3
        self.version_major = 0
        self.version_minor = 1
        self.header_fmt = "!BBBBqI"
        self.Header_Data = namedtuple(
            "header_data", "ID1 ID2 VER_MAJ VER_MIN START_TIME PACKET_NUM"
        )
        self.status_fmt = "!f?c20sIIIIfffffff?bfbbI"
        self.status_Data = namedtuple(
            "status_data",
            "VACUUM VACUUM_VALID CHRONY_STATUS CHRONY_NAME CHRONY_STRATUM CHRONY_POLL CHRONY_REACH REBOOT_COUNT DISK_PCT DISK_AVAILABLE MEMORY_PCT CPU_PCT BATTERY_VOLTAGE BATTERY_CURRENT BATTERY_PCT BATTERY_VALID NAV_SOURCE UPTIME DAQ_STATUS DAQ_ERRORS FRAME_COUNT",
        )

        self.chrony_stat_map = {
            "sync": "*",
            "valid": "+",
            "lost": "?",
            "false_ticker": "x",
            "variable": "~",
            "excluded": "-",
            "unknown": "u",
        }
        self.chrony_stat_map_inv = {v: k for k, v in self.chrony_stat_map.items()}
        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        if not data[0] == ord("A") or not data[1] == ord("S"):
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
        data = self.status_Data._make(
            struct.unpack(self.status_fmt, data[self.header_length_b :])
        )
        return data

    def decode(self, data):
        header = self.decode_header(data)
        d = self.decode_data(data, header)
        dc = DataContainer_Status(
            start_time=header.START_TIME,
            vacuum=d.VACUUM,
            vacuum_valid=d.VACUUM_VALID,
            chrony_status=self.chrony_stat_map_inv[d.CHRONY_STATUS.decode("ascii")],
            chrony_name=d.CHRONY_NAME,
            chrony_stratum=d.CHRONY_STRATUM,
            chrony_poll=d.CHRONY_POLL,
            chrony_reach=d.CHRONY_REACH,
            reboot_count=d.REBOOT_COUNT,
            disk_pct=d.DISK_PCT,
            disk_available=d.DISK_AVAILABLE,
            memory_pct=d.MEMORY_PCT,
            cpu_pct=d.CPU_PCT,
            battery_voltage=d.BATTERY_VOLTAGE,
            battery_current=d.BATTERY_CURRENT,
            battery_pct=d.BATTERY_PCT,
            battery_valid=d.BATTERY_VALID,
            nav_source=d.NAV_SOURCE,
            last_config_update=None,
            uptime=d.UPTIME,
            daq_status=d.DAQ_STATUS,
            daq_errors=d.DAQ_ERRORS,
            frame_count=d.FRAME_COUNT,
        )
        return dc

    def encode(self, dc, packet_number=None):
        if dc.frame_count is None:
            dc.frame_count = 0
        # print("Data container: " + repr(dc))
        if packet_number is None:
            packet_number = dc.frame_count

        frame_start_time = dc.get_start_time().astype(">i8")
        header = struct.pack(
            self.header_fmt,
            ord("A"),
            ord("S"),
            self.version_major,
            self.version_minor,
            frame_start_time,
            packet_number,
        )

        data = struct.pack(
            self.status_fmt,
            dc.vacuum,
            dc.vacuum_valid,
            self.chrony_stat_map[dc.chrony_status].encode("ascii"),
            dc.chrony_name.encode("ascii"),
            int(dc.chrony_stratum),
            int(dc.chrony_poll),
            int(dc.chrony_reach),
            int(dc.reboot_count),
            dc.disk_pct,
            dc.disk_available,
            dc.memory_pct,
            dc.cpu_pct,
            dc.battery_voltage,
            dc.battery_current,
            dc.battery_pct,
            dc.battery_valid,
            int(dc.nav_source),
            dc.uptime,
            int(dc.daq_status == "Running"),
            int(dc.daq_errors),
            int(dc.frame_count),
        )
        data_to_send = header + data
        return data_to_send
