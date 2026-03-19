from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from acbotics_pipeline.data_containers.data_container_window_with_sensors import (
    DataContainer_Window_With_Sensors,
)
import acbotics_pipeline.helpers.contract_helpers as ch
import numpy as np
import copy
import heapq

from dataclasses import dataclass, field
from typing import Any
from functools import partial
import multiprocessing

from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp

# TODO: This can probably be simplified now that we have SensorTimestamp with tick/wall time mapping built in


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    name: str = field(compare=False)
    item: Any = field(compare=False)


class CustomPriorityQueue:
    def __init__(self):
        self.lock = multiprocessing.Lock()
        self.heap = []

    def push(self, priority, name, value):
        with self.lock:
            heapq.heappush(self.heap, PrioritizedItem(priority, name, value))

    def pop(self):
        with self.lock:
            return heapq.heappop(self.heap)

    def peek(self):
        with self.lock:
            return self.heap[0] if self.heap else None

    def is_empty(self):
        with self.lock:
            return not self.heap

    def __len__(self):
        with self.lock:
            return len(self.heap)


class DataWindow:
    def __init__(
        self,
        acoustic_samples,
        num_channels,
        sample_rate,
        sensor_names,
        dtype=np.float32,
    ):
        self.active = False
        self.acoustic_samples = acoustic_samples
        self.num_channels = num_channels
        self.dtype = dtype
        self.reinit_buffer()
        self.acoustic_index = 0
        self.start_time = None
        self.sample_rate = sample_rate
        self.end_time = None
        self.tick_time = None
        self.tick_end = None
        self.sensor_names = sensor_names
        self._reset()

    def reinit_buffer(self):
        self.acoustic_data = np.zeros(
            (self.num_channels, self.acoustic_samples), dtype=self.dtype
        )

    def __repr__(self):
        return "Data Window (Active=%d)" % self.active

    def _reset(self):
        self.sensor_data = {}
        self.data_complete = {}
        for sn in self.sensor_names:
            self.sensor_data[sn] = []
            self.data_complete[sn] = False
        self._acoustics_complete = False
        self.active = False
        self.acoustic_index = 0

    @ch.argtype("sensor_timestamp", SensorTimestamp)
    def configure(self, sensor_timestamp):
        self.sensor_timestamp = sensor_timestamp
        self.start_time = self.sensor_timestamp.get_wall_time()
        self.tick_time = self.sensor_timestamp.get_tick_time()
        self.end_time = self.start_time + np.timedelta64(
            int(1e9 * float(self.acoustic_samples) / self.sample_rate), "ns"
        )
        self.tick_end = self.tick_time + int(
            1e9 * float(self.acoustic_samples) / self.sample_rate
        )
        self._reset()
        self.active = True

    def remaining_length(self):
        return self.acoustic_samples - self.acoustic_index

    def complete(self):
        complete = self.acoustics_complete()
        complete &= self.sensors_complete()
        return complete

    def acoustics_complete(self):
        return self._acoustics_complete

    def sensors_complete(self):
        complete = True
        for sen in self.data_complete.keys():
            if not self.data_complete[sen]:
                complete = False
                break
        return complete

    def add_acoustic_data(self, dc):
        channels = dc.data.shape[0]
        if not channels == self.num_channels:
            print(
                "Updating Data Window channels from %d to %d"
                % (self.num_channels, channels)
            )
            self.num_channels = channels
            self.reinit_buffer()

        data_len = dc._calculate_data_length()
        if data_len <= self.remaining_length():
            self.acoustic_data[
                :, self.acoustic_index : self.acoustic_index + data_len
            ] = dc.data
            self.acoustic_index += data_len
        else:
            available_len = self.remaining_length()
            self.acoustic_data[
                :, self.acoustic_index : self.acoustic_index + available_len
            ] = dc.data[:, 0:available_len]
            self.acoustic_index += available_len
        if self.remaining_length() == 0:
            self._acoustics_complete = True

    def add_sensor_data(self, name, dc):
        tick = dc.timestamp.get_tick_time()
        wall_time = dc.timestamp.get_wall_time()
        if tick < self.tick_time:
            return  # data before this window

        if name in self.sensor_data.keys():
            if tick > self.tick_end:
                self.data_complete[name] = True
                return  # data after this window
            dic = copy.copy(dc.value_dict)
            dic["timestamp"] = tick
            dic["host_epoch_sec"] = float(wall_time) / 1e9
            dic["data_epoch_nsec"] = (
                tick  # duplicate to play nice with nav utils. TODO: clean up
            )

            self.sensor_data[name].append(dic)

    def add_sensor_data_unticked(self, name, dc):
        ts = np.datetime64(dc.timestamp, "s")
        if ts < self.start_time:
            return  # data before this window

        if name in self.sensor_data.keys():
            if ts > self.end_time:
                self.data_complete[name] = True
                return  # data after this window
            dic = copy.copy(dc.value_dict)
            dic["timestamp"] = ts
            self.sensor_data[name].append(dic)

    def get_data_frame(self):
        return DataContainer_Window_With_Sensors(
            data=self.acoustic_data.copy(),
            sample_rate=self.sample_rate,
            sensors=self.sensor_data,
            start_time=self.sensor_timestamp,
            tick_time=self.tick_time,
        )


class Pr_Window(PR_Threaded_Process):
    def __init__(
        self,
        window_length_sec=11,
        overlap_sec=1,
        sensor_names=(),
        max_windows=3,
        num_channels=8,
    ):
        super().__init__()
        self.MAX_DATA_WINDOWS = max_windows
        self.sample_rate = 52734
        self.samples_per_window = int(self.sample_rate * window_length_sec)
        self.overlap_sec = overlap_sec
        self.num_channels = num_channels
        self.sensor_names = sensor_names
        self.window_dtype = np.float32
        self.base_window_idx = 0
        self.data_windows = [
            DataWindow(
                self.samples_per_window,
                self.num_channels,
                self.sample_rate,
                self.sensor_names,
                self.window_dtype,
            )
            for i in range(self.MAX_DATA_WINDOWS)
        ]
        self.pending_sensor_data = CustomPriorityQueue()
        self.pending_sensaor_data_unticked = CustomPriorityQueue()

    def handle_data(self, dc):
        # we know the windows are in order. Once we don't need to add data to one, we know we can stop checking.
        # print("Latest Acoustic Tick:" + repr(dc.start_time.get_tick_time()))

        next_start_time = None
        latest_tick = None
        latest_ts = None
        for ind_base in range(self.MAX_DATA_WINDOWS):
            ind = (ind_base + self.base_window_idx) % self.MAX_DATA_WINDOWS
            window = self.data_windows[ind]
            if not window.active:
                if next_start_time is None:
                    window.configure(dc.start_time)
                elif (
                    dc.start_time.get_wall_time() >= next_start_time
                ):  # should we add the dc length here?
                    window.configure(dc.start_time)
                else:
                    break  # we are Done
            assert window.active
            next_start_time = window.end_time - np.timedelta64(
                int(1e9 * self.overlap_sec), "ns"
            )
            if not dc.start_time.get_wall_time() >= window.start_time:
                print("Warning Backwards Time step. Resetting window")
                window._reset()
            window.add_acoustic_data(dc)
            latest_tick = dc.tick_time
            latest_ts = dc.start_time.get_wall_time()
            if window.complete():
                print("Window done")
                self.send_data(window.get_data_frame())
                window._reset()
                self.base_window_idx = (
                    self.base_window_idx + 1
                ) % self.MAX_DATA_WINDOWS
                continue
        # now see if any of our sensors can be added with a TICK timebase.
        while True:
            if self.pending_sensor_data.is_empty():
                break
            next_sensor_tick = self.pending_sensor_data.peek().priority
            if next_sensor_tick < latest_tick:
                next_sensor_queue_item = self.pending_sensor_data.pop()
                next_sensor = next_sensor_queue_item.item
                next_sensor_name = next_sensor_queue_item.name
                next_sensor_tick = next_sensor_queue_item.priority
                # note, this may lag one acoustic packet behind.
                for ind_base in range(self.MAX_DATA_WINDOWS):
                    ind = (ind_base + self.base_window_idx) % self.MAX_DATA_WINDOWS
                    window = self.data_windows[ind]
                    if not window.active:
                        break
                    # if next_sensor.timestamp >= window.tick_end:

                    #     continue  # window is older than the new sensor data. Check next one
                    # if next_sensor.timestamp <= window.tick_end:

                    window.add_sensor_data(next_sensor_name, next_sensor)
                    # else:
                    #     break  # we reached the end
            else:
                break

        # now see if any of our sensors can be added with a nontick timebase.
        while True:
            if self.pending_sensaor_data_unticked.is_empty():
                break
            next_sensor_ts = self.pending_sensaor_data_unticked.peek().priority
            if np.datetime64(next_sensor_ts, "s") < latest_ts:
                next_sensor_queue_item = self.pending_sensaor_data_unticked.pop()
                next_sensor = next_sensor_queue_item.item
                next_sensor_name = next_sensor_queue_item.name
                next_sensor_ts = next_sensor_queue_item.priority
                # note, this may lag one acoustic packet behind.
                for ind_base in range(self.MAX_DATA_WINDOWS):
                    ind = (ind_base + self.base_window_idx) % self.MAX_DATA_WINDOWS
                    window = self.data_windows[ind]
                    if not window.active:
                        break
                    # if next_sensor.timestamp >= window.tick_end:

                    #     continue  # window is older than the new sensor data. Check next one
                    # if next_sensor.timestamp <= window.tick_end:

                    window.add_sensor_data_unticked(next_sensor_name, next_sensor)
                    # else:
                    #     break  # we reached the end
            else:
                break

    def handle_sensor_data(self, name, dc):
        # if dc.timestamp_src == "TICK":
        if not "COMP" in dc.timestamp.get_all_wall_times():
            print("No COMP time for %s. May not have time sync yet." % (name,))
            return
        if "TICK" in dc.timestamp.get_all_tick_times():
            tick = dc.timestamp.get_tick_time()
            # print("%s: Tick=%d" % (name, tick))
            self.pending_sensor_data.push(tick, name, dc)
        else:
            print("Warning. No tick data for sensor in window. %s" % (name))
        # else:
        #     self.pending_sensaor_data_unticked.push(dc.timestamp, name, dc)

    def get_sensor_callback(self, name):
        return partial(self.handle_sensor_data, name)
