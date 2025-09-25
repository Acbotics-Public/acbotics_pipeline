#!/usr/bin/python3
from abc import ABC
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import queue
import multiprocessing
import threading
import time
from uldaq import (
    get_daq_device_inventory,
    DaqDevice,
    InterfaceType,
    AiInputMode,
    Range,
    AInFlag,
    ScanOption,
    ScanStatus,
    AInScanFlag,
    create_float_buffer,
    create_int_buffer,
    DaqEventType,
    EventCallbackArgs,
)
import pyprctl


class In_Mcc_DAQ_Event_Raw(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(
        self,
        sample_rate,
        start_channel,
        num_channels,
        start_time,
        device_index=0,
        as_process=False,
        auto_start=True,
        voltage_range=5,
    ):
        self.callbacks = []
        self.as_process = as_process
        if as_process:
            self.resultframes = multiprocessing.Queue()
            self.multi_process = multiprocessing.Process(
                target=self.run_process,
                args=(
                    self.resultframes,
                    sample_rate,
                    start_channel,
                    num_channels,
                    start_time,
                    device_index,
                    voltage_range,
                ),
            )
            self.thread = threading.Thread(target=self.run_output_thread)
        else:
            self.dataframes = queue.Queue()
            self.thread = threading.Thread(
                target=self.run_thread,
                args=(
                    sample_rate,
                    start_channel,
                    num_channels,
                    start_time,
                    device_index,
                    voltage_range,
                ),
            )

        self.stop = False
        self.waiting = True
        self.started = False
        if auto_start:
            self.start()

    def start(self, dc=None):  # extra argument to allow callbacks
        self.stop = False
        self.thread.start()
        if self.as_process:
            self.multi_process.start()
        self.started = True

    def __del__(self):
        if self.daq_device:
            if self.daq_device.is_connected():
                self.daq_device.disconnect()
            self.daq_device.release()

    def is_waiting(self):
        return True

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return 1

    def get_sample_rate(self):
        return self.sample_rate

    def add_callback(self, function):
        self.callbacks.append(function)

    def _add_sample(self, t):
        self.data_buffer.append(self._calculate(t))

    def callback(self, event_callback_args: EventCallbackArgs):
        ts = time.process_time()
        status, transfer_status = self.ai_device.get_scan_status()
        total_samples_per_channel = transfer_status.current_scan_count
        #        print("Total samples= " + repr(total_samples_per_channel))
        #        print("Delta = " + repr(total_samples_per_channel - self.last_total_samples))
        #        print(event_callback_args.event_data)
        # self.last_total_samples = total_samples_per_channel
        index = transfer_status.current_index
        # get the index for the last complete transfer
        mod_index = index - (index % self.num_chans)
        # print("mod_ind: " + repr(mod_index) + "last ind: " + repr(self.last_index))
        # print("delta:" + repr(mod_index - self.last_index))
        if mod_index > self.last_index:
            # no wrap around
            new_data = self.data[self.last_index : mod_index]
        else:
            # wrap around
            print("wrap")
            new_data = self.data[self.last_index :]
            new_data.extend(self.data[0:mod_index])
        self.last_index = mod_index
        # print("daq callback process time before convert: " + repr(time.process_time() - ts))
        # np_data = np.array(new_data, dtype=np.uint16).reshape( -1, self.num_chans).transpose()

        np_data = np.fromiter(new_data, dtype=np.uint16)
        # print("daq callback process time before reshape: " + repr(time.process_time()-ts))
        np_data = np_data.reshape(-1, self.num_chans).transpose()
        # print("daq callback process time before put: " + repr(time.process_time() - ts))
        self.new_data_frames.put(np_data)
        # print("daq callback process time: " + repr(time.process_time() - ts))
        print(
            "Seconds of data processed: "
            + repr((total_samples_per_channel - self.last_total_samples) / 50000)
        )
        self.last_total_samples = total_samples_per_channel

    def initialize_process(
        self,
        sample_rate,
        start_channel,
        num_channels,
        start_time,
        device_index,
        voltage_range=5,
    ):
        self.sample_rate = sample_rate
        self.start_time = start_time
        # self.front_half = True
        self.last_index = 0
        self.last_total_samples = 0
        self.num_chans = num_channels
        devices = get_daq_device_inventory(InterfaceType.USB)
        self.daq_device = DaqDevice(devices[device_index])
        self.daq_device.connect()

        self.ai_device = self.daq_device.get_ai_device()
        self.new_data_frames = queue.Queue()

        ai_info = self.ai_device.get_info()
        self.buffer_sample_size = (
            sample_rate * 10
        )  # 1 second of data per scan (1/2 second per ping pong buffer)
        self.data = create_float_buffer(self.num_chans, self.buffer_sample_size)
        eventTypes = (
            DaqEventType.ON_DATA_AVAILABLE
            | DaqEventType.ON_INPUT_SCAN_ERROR
            | DaqEventType.ON_END_OF_INPUT_SCAN
        )
        availableSampleCount_1 = int(self.sample_rate / 4)

        err = self.daq_device.enable_event(
            eventTypes, availableSampleCount_1, self.callback, None
        )
        # err2 = self.daq_device.enable_event(eventTypes, availableSampleCount_2, self.callback, None);

        analog_range = Range.BIP5VOLTS
        if voltage_range == 5:
            analog_range = Range.BIP5VOLTS
        elif voltage_range == 10:
            analog_range = Range.BIP10VOLTS
        elif voltage_range == 2:
            analog_range = Range.BIP2VOLTS
        elif voltage_range == 1:
            analog_range = Range.BIP1VOLTS
        else:
            print("Warning Invalid range setting. Defaulting range options")

        self.ai_device.a_in_scan(
            low_channel=start_channel,
            high_channel=start_channel + num_channels - 1,
            input_mode=AiInputMode.SINGLE_ENDED,
            analog_range=analog_range,
            samples_per_channel=self.buffer_sample_size,
            rate=self.sample_rate,
            options=ScanOption.CONTINUOUS,
            flags=AInScanFlag.NOSCALEDATA,
            data=self.data,
        )
        self.next_start_time = self.start_time

    def run_thread(
        self,
        sample_rate,
        start_channel,
        num_channels,
        start_time,
        device_index,
        voltage_range,
    ):
        pyprctl.set_name("MCC THREAD")
        self.initialize_process(
            sample_rate,
            start_channel,
            num_channels,
            start_time,
            device_index,
            voltage_range,
        )
        while True:
            new_data = self.new_data_frames.get()
            st = time.process_time()
            dc = DataContainer_Constant_Rate(
                new_data, self.sample_rate, self.next_start_time, start_count=0
            )
            self.next_start_time = self.next_start_time + np.timedelta64(
                int(1e9 / self.sample_rate) * new_data.shape[1], "ns"
            )
            self.send_data(dc)

    def run_process(
        self,
        result_queue,
        sample_rate,
        start_channel,
        num_channels,
        start_time,
        device_index,
        voltage_range,
    ):
        pyprctl.set_name("MCC PROC")
        self.initialize_process(
            sample_rate,
            start_channel,
            num_channels,
            start_time,
            device_index,
            voltage_range,
        )

        while True:
            new_data = self.new_data_frames.get()
            dc = DataContainer_Constant_Rate(
                new_data, self.sample_rate, self.next_start_time
            )
            self.next_start_time = self.next_start_time + np.timedelta64(
                int(1e9 / self.sample_rate * new_data.shape[1]), "ns"
            )
            result_queue.put(dc)

    def send_data(self, data_to_send):
        for c in self.callbacks:
            c(data_to_send)

    def run_output_thread(self):
        """This thread watches for data back from the process. When data comes back, it will call send
        data to make the callbacks"""
        pyprctl.set_name("MCC Output Thread")

        while True:
            dc = self.resultframes.get()
            if not dc is None:
                self.send_data(dc)

    def get_daq_status(self):
        if not self.started:
            return "Waiting"
        return "Running"

    def get_daq_errors(self):
        return 0

    def process(self, process_time):
        pass
