from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from acbotics_pipeline.data_containers.data_container_window_with_sensors import (
    DataContainer_Window_With_Sensors,
)
import numpy as np
import copy
import heapq

from dataclasses import dataclass, field
from typing import Any
from functools import partial


@dataclass(order=True)
class PrioritizedItem:
    priority: int
    name: str = field(compare=False)
    item: Any = field(compare=False)


class CustomPriorityQueue:
    def __init__(self):
        self.heap = []

    def push(self, priority, name, value):
        heapq.heappush(self.heap, PrioritizedItem(priority, name, value))

    def pop(self):
        return heapq.heappop(self.heap)

    def peek(self):
        return self.heap[0] if self.heap else None

    def is_empty(self):
        return not self.heap

    def __len__(self):
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
        print((self.acoustic_samples, num_channels))
        self.acoustic_data = np.zeros(
            (num_channels, self.acoustic_samples), dtype=dtype
        )
        self.acoustic_index = 0
        self.start_time = None
        self.sample_rate = sample_rate
        self.end_time = None
        self.tick_time = None
        self.tick_end = None
        self.sensor_names = sensor_names
        self._reset()

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

    def configure(self, start_time, tick_time):
        self.start_time = start_time
        self.tick_time = tick_time
        self.end_time = self.start_time + np.timedelta64(
            int(1e9 * float(self.acoustic_samples) / self.sample_rate), "ns"
        )
        self.tick_end = tick_time + int(
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
        if dc.timestamp < self.tick_time:
            return  # data before this window

        if name in self.sensor_data.keys():
            if dc.timestamp > self.tick_end:
                self.data_complete[name] = True
                return  # data after this window
            dic = copy.copy(dc.value_dict)
            dic["timestamp"] = dc.timestamp
            self.sensor_data[name].append(dic)

    def get_data_frame(self):
        return DataContainer_Window_With_Sensors(
            data=self.acoustic_data,
            sample_rate=self.sample_rate,
            sensors=self.sensor_data,
            start_time=self.start_time,
            tick_time=self.tick_time,
        )


class Pr_Window(PR_Threaded_Process):
    def __init__(self, window_length_sec=11, overlap_sec=1, sensor_names=()):
        super().__init__()
        self.MAX_DATA_WINDOWS = 3
        self.sample_rate = 52734
        self.samples_per_window = self.sample_rate * window_length_sec
        self.overlap_sec = overlap_sec
        self.num_channels = 8
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

    def handle_data(self, dc):
        # we know the windows are in order. Once we don't need to add data to one, we know we can stop checking.
        next_start_time = None
        latest_tick = None
        for ind_base in range(self.MAX_DATA_WINDOWS):
            ind = (ind_base + self.base_window_idx) % self.MAX_DATA_WINDOWS
            window = self.data_windows[ind]
            if not window.active:
                if next_start_time is None:
                    window.configure(dc.start_time, dc.tick_time)
                elif (
                    dc.start_time >= next_start_time
                ):  # should we add the dc length here?
                    window.configure(dc.start_time, dc.tick_time)
                else:
                    break  # we are Done
            assert window.active
            next_start_time = window.end_time - self.overlap_sec
            if not dc.start_time >= window.start_time:
                print("Warning Backwards Time step. Resetting window")
                window._reset()
            window.add_acoustic_data(dc)
            latest_tick = dc.tick_time
            if window.complete():
                self.send_data(window.get_data_frame())
                window._reset()
                self.base_window_idx = (
                    self.base_window_idx + 1
                ) % self.MAX_DATA_WINDOWS
                continue
        # now see if any of our sensors can be added.
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

    def handle_sensor_data(self, name, dc):
        self.pending_sensor_data.push(dc.timestamp, name, dc)

    def get_sensor_callback(self, name):
        return partial(self.handle_sensor_data, name)
