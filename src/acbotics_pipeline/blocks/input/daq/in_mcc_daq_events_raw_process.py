#!/usr/bin/python3
from abc import ABC
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import queue
import threading
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
        self, sample_rate, start_channel, num_channels, start_time, device_index=0
    ):
        self.sample_rate = sample_rate
        self.callbacks = []
        self.start_time = start_time
        self.front_half = True
        self.num_chans = num_channels
        devices = get_daq_device_inventory(InterfaceType.USB)
        self.daq_device = DaqDevice(devices[device_index])
        self.daq_device.connect()

        self.ai_device = self.daq_device.get_ai_device()
        self.new_data_frames = queue.Queue()

        ai_info = self.ai_device.get_info()
        self.buffer_sample_size = (
            sample_rate  # 1 second of data per scan (1/2 second per ping pong buffer)
        )
        self.data = create_float_buffer(self.num_chans, self.buffer_sample_size)
        eventTypes = (
            DaqEventType.ON_DATA_AVAILABLE
            | DaqEventType.ON_INPUT_SCAN_ERROR
            | DaqEventType.ON_END_OF_INPUT_SCAN
        )
        availableSampleCount_1 = int(self.sample_rate / 8)

        err = self.daq_device.enable_event(
            eventTypes, availableSampleCount_1, self.callback, None
        )
        # err2 = self.daq_device.enable_event(eventTypes, availableSampleCount_2, self.callback, None);

        self.ai_device.a_in_scan(
            low_channel=start_channel,
            high_channel=start_channel + num_channels - 1,
            input_mode=AiInputMode.SINGLE_ENDED,
            analog_range=Range.BIP5VOLTS,
            samples_per_channel=self.buffer_sample_size,
            rate=self.sample_rate,
            options=ScanOption.CONTINUOUS,
            flags=AInScanFlag.NOSCALEDATA,
            data=self.data,
        )
        self.next_start_time = self.start_time
        self.thread = threading.Thread(target=self.run_thread)
        self.thread.start()

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
        mid_pt = int(self.buffer_sample_size / 2 * self.num_chans)

        status, transfer_status = self.ai_device.get_scan_status()
        #        print('cb: ' + repr(transfer_status.current_index))
        # Ping pong the buffer. If halfway through, read first half. If less than half, read second half.
        if self.front_half and transfer_status.current_index > mid_pt:
            # read front of data
            self.front_half = False
            new_data = self.data[:mid_pt]
        #            print("front")
        elif (not self.front_half) and transfer_status.current_index < mid_pt:
            # read the back half of data
            self.front_half = True
            new_data = self.data[mid_pt:]
        #            print("back")
        else:
            return
        self.new_data_frames.put(
            np.array(new_data, dtype=np.uint16).reshape(-1, self.num_chans).transpose()
        )

    def run_thread(self):
        pyprctl.set_name("MCC THREAD")
        while True:
            new_data = self.new_data_frames.get()
            dc = DataContainer_Constant_Rate(
                new_data, self.sample_rate, self.next_start_time
            )
            self.next_start_time = self.next_start_time + np.timedelta64(
                int(1e9 / self.sample_rate * self.buffer_sample_size / 2), "ns"
            )
            #           print("sending daq data")
            print(new_data.shape)
            for c in self.callbacks:
                c(dc)

    def get_daq_status(self):
        pass

    def process(self, process_time):
        pass
