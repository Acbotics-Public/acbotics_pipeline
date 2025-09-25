import icontract
import numpy as np
from data_containers.data_container_status import DataContainer_Status
import math
import time
import subprocess
import sys

import uptime
from acbotics_pipeline.system.chrony import get_active_chrony_status
from acbotics_pipeline.system.disk import get_disk_percentage
from acbotics_pipeline.system.disk import get_disk_available
from acbotics_pipeline.system.memory import get_memory_usage
from acbotics_pipeline.system.cpu import get_cpu_percent

import threading


class In_Status_Reader:
    def __init__(
        self,
        output_rate=1,
        daq_block=None,
        reboot_count_file="/opt/acbotics/status/reboot_count",
        pressure_sensor=None,
    ):
        self.last_message_time = None
        self.daq_block = daq_block
        self.reboot_count_file = reboot_count_file
        self.callbacks = []
        self.output_rate = output_rate
        self.pressure_sensor = pressure_sensor
        self.thread = threading.Thread(target=self.run_thread)
        self.thread.start()

    def is_waiting(self):
        return True

    def add_callback(self, function):
        self.callbacks.append(function)

    def read_vacuum(self):
        if self.pressure_sensor is None:
            return None
        vals = self.pressure_sensor.read_sensor()
        return vals["pressure_pa"]

    def read_chrony_status(self):
        return get_active_chrony_status()

    def read_reboot_count(self):
        reboot_count = -1
        try:
            with open(self.reboot_count_file, "r") as f:
                line = f.readline()
                reboot_count = int(line)
        except Exception as e:
            print("Exception reading reboot count: " + repr(e))
        return reboot_count

    def get_daq_status(self):
        if self.daq_block is None:
            return 0
        return self.daq_block.get_daq_status()

    def get_daq_errors(self):
        if self.daq_block is None:
            return 0
        return self.daq_block.get_daq_errors()

    def process(self, process_time):
        pass

    def run_thread(self):
        while True:
            vacuum = self.read_vacuum()
            vacuum_valid = True
            if vacuum is None:
                vacuum = 0
                vacuum_valid = False
            c_stat = self.read_chrony_status()
            # print(c_stat)
            dc = DataContainer_Status(
                start_time=np.datetime64(time.time_ns(), "ns"),
                vacuum=vacuum,
                vacuum_valid=vacuum_valid,
                chrony_status=c_stat["state"],
                chrony_name=c_stat["name"],
                chrony_stratum=c_stat["stratum"],
                chrony_poll=c_stat["poll"],
                chrony_reach=c_stat["reach"],
                reboot_count=self.read_reboot_count(),
                disk_pct=get_disk_percentage(),
                disk_available=get_disk_available(),
                memory_pct=get_memory_usage(),
                cpu_pct=get_cpu_percent(),
                battery_voltage=0,
                battery_current=0,
                battery_pct=0,
                battery_valid=False,
                nav_source=-1,
                daq_status=self.get_daq_status(),
                daq_errors=self.get_daq_errors(),
                last_config_update=None,
                uptime=uptime.uptime(),
            )

            print("Sending Status")
            for c in self.callbacks:
                c(dc)
            time.sleep(1 / self.output_rate)
