"""
Created on Mar 7, 2022

@author: sam
"""

from abc import ABC, abstractmethod
import icontract
from .data_container import DataContainer
import numpy as np

# from pprint import pprint


class DataContainer_Status(DataContainer):
    def __init__(
        self,
        start_time,
        vacuum=0,
        vacuum_valid=False,
        chrony_status="unknown",
        chrony_name="",
        chrony_stratum=-1,
        chrony_poll=-1,
        chrony_reach=-1,
        reboot_count=-1,
        disk_pct=-1,
        disk_available=-1,
        memory_pct=-1,
        cpu_pct=-1,
        battery_voltage=0,
        battery_current=0,
        battery_pct=0,
        battery_valid=False,
        nav_source=-1,
        last_config_update=None,
        uptime=-1,
        daq_status=0,
        daq_errors=0,
        frame_count=0,
    ):
        self.vacuum = vacuum
        self.vacuum_valid = vacuum_valid
        self.start_time = start_time
        self.chrony_status = chrony_status
        self.chrony_name = chrony_name
        self.chrony_stratum = chrony_stratum
        self.chrony_poll = chrony_poll
        self.chrony_reach = chrony_reach
        self.reboot_count = reboot_count
        self.disk_pct = disk_pct
        self.disk_available = disk_available
        self.memory_pct = memory_pct
        self.cpu_pct = cpu_pct
        self.battery_voltage = battery_voltage
        self.battery_current = battery_current
        self.battery_pct = battery_pct
        self.battery_valid = battery_valid
        self.nav_source = nav_source
        # self.last_config_update
        self.uptime = uptime
        self.daq_status = daq_status
        self.daq_errors = daq_errors
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
        # pprint(self.__dict__, indent=2)
        return """DataContainer_Status:
        vacuum: %f
        vacuum_valid: %d
        chrony_status %s
        chrony_name: %s
        chrony_stratum: %d
        chrony_poll: %d
        chrony_reach: %d
        reboot_count: %d
        disk_pct:  %f
        disk_available:  %f
        memory_pct: %f
        cpu_pct: %f
        battery_voltage: %f
        battery_current: %f
        battery_pct: %f
        battery_valid: %d
        nav_source: %d
        uptime: %f
        daq_status: %d
        daq_errors: %d
        start_time: %f
        frame_count %d
        """ % (
            self.vacuum,
            self.vacuum_valid,
            self.chrony_status,
            self.chrony_name,
            self.chrony_stratum,
            self.chrony_poll,
            self.chrony_reach,
            self.reboot_count,
            self.disk_pct,
            self.disk_available,
            self.memory_pct,
            self.cpu_pct,
            self.battery_voltage,
            self.battery_current,
            self.battery_pct,
            self.battery_valid,
            self.nav_source,
            self.uptime,
            self.daq_status == "Running",
            self.daq_errors,
            self.start_time,
            self.frame_count,
        )
