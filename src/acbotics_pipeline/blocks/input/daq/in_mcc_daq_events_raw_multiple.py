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
    daq_device,
)
import pyprctl
from time import sleep


class DAQ_Helper:
    def __init__(self, daq_device, output_queue):
        self.daq_device = daq_device
        self.output_queue = output_queue

    def __del__(self):
        if self.daq_device:
            if self.daq_device.is_connected():
                self.daq_device.disconnect()
            self.daq_device.release()

    @icontract.require(lambda num_channels: isinstance(num_channels, int))
    @icontract.require(lambda num_channels: num_channels > 0)
    @icontract.require(lambda start_channel: isinstance(start_channel, int))
    @icontract.require(lambda start_channel: start_channel >= 0)
    @icontract.require(lambda sample_rate: sample_rate > 0)
    @icontract.require(lambda follower: isinstance(follower, bool))
    def initialize_daq(
        self,
        sample_rate,
        start_channel,
        num_channels,
        start_time,
        voltage_range=5,
        follower=False,
    ):
        self.sample_rate = sample_rate
        self.start_time = start_time
        self.follower = follower
        # self.front_half = True
        self.last_index = 0
        self.last_total_samples = 0
        self.num_chans = num_channels

        self.ai_device = self.daq_device.get_ai_device()

        self.buffer_sample_size = sample_rate * 10
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
        self.enter_count = 0
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

        options = ScanOption.CONTINUOUS
        # For the follower, use the external clock
        if self.follower:
            options |= ScanOption.EXTCLOCK
        else:
            options |= ScanOption.PACEROUT

        self.ai_device.a_in_scan(
            low_channel=start_channel,
            high_channel=start_channel + num_channels - 1,
            input_mode=AiInputMode.SINGLE_ENDED,
            analog_range=analog_range,
            samples_per_channel=self.buffer_sample_size,
            rate=self.sample_rate,
            options=options,
            flags=AInScanFlag.NOSCALEDATA,
            data=self.data,
        )
        self.next_start_time = self.start_time

    def callback(self, event_callback_args: EventCallbackArgs):
        if not self.enter_count == 0:
            print("double enter")
        self.enter_count += 1
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
            # print('wrap')
            # todo. Try preallocating array to avoid needing to extend
            new_data = self.data[self.last_index :]
            new_data.extend(self.data[0:mod_index])
        self.last_index = mod_index
        # print("daq callback process time before convert: " + repr(time.process_time() - ts))
        # np_data = np.array(new_data, dtype=np.uint16).reshape( -1, self.num_chans).transpose()

        np_data = np.fromiter(new_data, dtype=np.uint16)
        # print("daq callback process time before reshape: " + repr(time.process_time()-ts))
        np_data = np_data.reshape(-1, self.num_chans).transpose()
        # print("daq callback process time before put: " + repr(time.process_time() - ts))
        self.output_queue.put((total_samples_per_channel, np_data))
        # print("daq callback process time: " + repr(time.process_time() - ts))
        # print("Seconds of data processed: " + repr((total_samples_per_channel - self.last_total_samples)/50000))
        # print("Follower=" + repr(self.follower))
        if not total_samples_per_channel - self.last_total_samples == np_data.shape[1]:
            print(
                "Change in total samples: %d, amount of data received: %d"
                % (
                    total_samples_per_channel - self.last_total_samples,
                    np_data.shape[1],
                )
            )
        self.last_total_samples = total_samples_per_channel
        self.enter_count -= 1


class Data_Frame:
    @icontract.require(
        lambda num_channels, num_daqs: num_channels % num_daqs == 0,
        "Must have same number of channels on each daq",
    )
    @icontract.require(lambda num_channels: isinstance(num_channels, int))
    @icontract.require(lambda num_daqs: isinstance(num_daqs, int))
    @icontract.require(lambda samples_per_channel: isinstance(samples_per_channel, int))
    @icontract.require(lambda samples_per_channel: samples_per_channel > 0)
    @icontract.require(lambda num_channels: num_channels > 0)
    def __init__(self, num_channels, samples_per_channel, num_daqs=2):
        self.num_channels = num_channels
        self.samples_per_channel = samples_per_channel
        self.num_daqs = num_daqs
        self.data = np.zeros((num_channels, samples_per_channel), dtype=np.uint16)
        self.channel_indexes = [0] * num_daqs

    @icontract.ensure(lambda result: isinstance(result, int))
    def get_channels_per_daq(self):
        return int(self.num_channels / self.num_daqs)

    @icontract.require(lambda self, channel: channel < self.num_channels)
    @icontract.require(
        lambda self, new_data: new_data.shape[0] == self.num_channels / self.num_daqs
    )
    @icontract.ensure(lambda result: isinstance(result, int))
    @icontract.ensure(lambda result: result >= 0)
    def add_data(self, channel, new_data):
        new_samples = new_data.shape[1]
        remaining_sample_slots = (
            self.samples_per_channel - self.channel_indexes[channel]
        )
        channel_start = self.get_channels_per_daq() * channel
        channel_end = channel_start + self.get_channels_per_daq()
        sample_start = self.channel_indexes[channel]
        next_unused_sample = 0
        if new_samples > remaining_sample_slots:
            sample_end = self.samples_per_channel
            self.data[channel_start:channel_end, sample_start:sample_end] = new_data[
                :, 0:remaining_sample_slots
            ]
            self.channel_indexes[channel] = sample_end
            next_unused_sample = remaining_sample_slots
        else:
            sample_end = sample_start + new_samples
            self.data[channel_start:channel_end, sample_start:sample_end] = new_data
            self.channel_indexes[channel] = sample_end
            next_unused_sample = new_samples
        # print(self.channel_indexes)
        # print("Next usused sample for channel %d is %d"%(channel, next_unused_sample))
        return next_unused_sample

    @icontract.ensure(lambda result: isinstance(result, bool))
    def is_complete(self):
        for c in self.channel_indexes:
            if c < self.samples_per_channel:
                return False
        return True

    @icontract.require(lambda daq: isinstance(daq, int))
    @icontract.require(lambda daq: daq >= 0)
    @icontract.require(lambda self, daq: daq < self.num_daqs)
    @icontract.ensure(lambda result: isinstance(result, bool))
    def is_daq_full(self, daq):
        return not self.channel_indexes[daq] < self.samples_per_channel


class In_Mcc_DAQ_Event_Raw_Multiple(ABC):
    """Assumes that no other mcc daqs are connected to the system"""

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
        num_daqs=2,
        as_process=False,
        auto_start=True,
        voltage_range=5,
    ):
        self.callbacks = []
        self.num_daqs = num_daqs
        self.num_channels = num_channels
        self.as_process = as_process
        self.next_start_time = start_time

        if as_process:
            self.resultframes = multiprocessing.Queue()
            self.data_queue_leader = multiprocessing.Queue()
            self.data_queue_follower = multiprocessing.Queue()
            self.multi_process = multiprocessing.Process(
                target=self.run_process,
                args=(
                    self.resultframes,
                    sample_rate,
                    start_channel,
                    num_channels,
                    start_time,
                    voltage_range,
                ),
            )
            self.thread = threading.Thread(target=self.run_output_thread)
        else:
            self.dataframes = queue.Queue()
            self.data_queue_leader = queue.Queue()
            self.data_queue_follower = queue.Queue()
            self.thread = threading.Thread(
                target=self.run_thread,
                args=(
                    sample_rate,
                    start_channel,
                    num_channels,
                    start_time,
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
        self.frames = []
        self.start_time = start_time
        # self.front_half = True
        self.last_index = 0
        self.last_total_samples = 0
        self.num_chans = num_channels
        devices = get_daq_device_inventory(InterfaceType.USB)

        self.daq_1 = None
        self.daq_2 = None
        # TODO: identify devices and order here
        print(devices)
        for dev in devices:
            daq_device = DaqDevice(dev)
            daq_device.connect()
            dio = daq_device.get_dio_device()
            id_val = (dio.d_in(1) & 0x80) >> 7
            if id_val:
                self.daq_2 = DAQ_Helper(daq_device, self.data_queue_follower)
            else:
                self.daq_1 = DAQ_Helper(daq_device, self.data_queue_leader)

        if self.daq_1 is None or self.daq_2 is None:
            print("Failed to find 2 DAQs")
            return
        # Initialize follower first, so it is ready when leader starts clocking
        print("starting follower")

        self.daq_2.initialize_daq(
            sample_rate=sample_rate,
            start_channel=start_channel,
            num_channels=int(num_channels / self.num_daqs),
            start_time=start_time,
            voltage_range=voltage_range,
            follower=True,
        )
        sleep(2)
        print("starting leader")

        self.daq_1.initialize_daq(
            sample_rate=sample_rate,
            start_channel=start_channel,
            num_channels=int(num_channels / self.num_daqs),
            start_time=start_time,
            voltage_range=voltage_range,
            follower=False,
        )

    def run_thread(
        self, sample_rate, start_channel, num_channels, start_time, voltage_range
    ):
        pyprctl.set_name("MCC THREAD")
        self.initialize_process(
            sample_rate, start_channel, num_channels, start_time, voltage_range
        )
        while True:
            # read queue 1
            # read queue 2
            # print("Waiting for data")
            (end_idx_follower, data_follower) = self.data_queue_follower.get()

            (end_idx_leader, data_leader) = self.data_queue_leader.get()
            if not end_idx_follower == end_idx_leader:
                print(
                    "mismatch of end idx: " + repr((end_idx_leader, end_idx_follower))
                )

            # print((end_idx_leader, end_idx_follower))

            # fill current frame. If full, add to next
            daq_ind = 0
            next_start_ind = 0
            for f in self.frames:
                if not f.is_daq_full(daq_ind):
                    next_start_ind += f.add_data(
                        daq_ind, data_leader[:, next_start_ind:]
                    )
                if next_start_ind >= data_leader.shape[1]:
                    break
            while next_start_ind < data_leader.shape[1]:
                f = Data_Frame(
                    num_channels=self.num_channels,
                    samples_per_channel=self.sample_rate,  # TODO: Make configurable?
                    num_daqs=self.num_daqs,
                )
                self.frames.append(f)
                next_start_ind += f.add_data(daq_ind, data_leader[:, next_start_ind:])

            # fill current frame. If full, add to next
            daq_ind = 1
            next_start_ind = 0
            for f in self.frames:
                if not f.is_daq_full(daq_ind):
                    next_start_ind += f.add_data(
                        daq_ind, data_follower[:, next_start_ind:]
                    )
                if next_start_ind >= data_follower.shape[1]:
                    break
            while next_start_ind < data_follower.shape[1]:
                f = Data_Frame(
                    num_channels=self.num_channels,
                    samples_per_channel=self.sample_rate,  # TODO: Make configurable?
                    num_daqs=self.num_daqs,
                )
                self.frames.append(f)
                next_start_ind += f.add_data(daq_ind, data_follower[:, next_start_ind:])

            while True:
                if len(self.frames) == 0:
                    break
                # print(self.frames)
                # print([f.is_complete() for f in self.frames])

                if self.frames[0].is_complete():
                    f = self.frames.pop(0)
                    assert f.is_complete()
                    dc = DataContainer_Constant_Rate(
                        f.data, self.sample_rate, self.next_start_time
                    )
                    self.next_start_time = self.next_start_time + np.timedelta64(
                        int(1e9 / self.sample_rate) * f.data.shape[1], "ns"
                    )
                    self.send_data(dc)

                    # send frame here
                else:
                    break

    def run_process(
        self,
        result_queue,
        sample_rate,
        start_channel,
        num_channels,
        start_time,
        voltage_range,
    ):
        pyprctl.set_name("MCC PROC")
        self.initialize_process(
            sample_rate, start_channel, num_channels, start_time, voltage_range
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
