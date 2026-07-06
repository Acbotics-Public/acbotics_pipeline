from acbotics_pipeline.data_containers import (
    DataContainer_Sensor,
    DataContainer_Constant_Rate,
)
from abc import ABC, abstractmethod

import time

import os
import numpy as np

import datetime
import pandas as pd

from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp


class DataFile:
    def __init__(self, filename, path, cache_path, file_time):
        self.filename = filename
        self.path = path
        self.cache_path = cache_path
        self.file_time = file_time
        self.start_tick = None
        self.end_tick = None
        self.host_time_start = None
        self.host_time_end = None
        self.num_samples = 0

    def __repr__(self):
        return (
            "Data File: \r\n\tname=%s\r\n\tpath=%s\r\n\tnum_samples=%d\r\n\tfile_time=%s\r\n\tStart_tick=%s\r\n\tEnd_tick=%s\r\n\tHost_Time_Start=%s\r\n\tHost_Time_Stop=%s\r\n"
            % (
                self.filename,
                self.path,
                self.num_samples,
                self.file_time.strftime("%Y%m%d-%H%M%S"),
                self.start_tick,
                self.end_tick,
                self.host_time_start,
                self.host_time_end,
            )
        )

    def _load_csv_file(self, force_cache_reload=False):
        if os.path.exists(self.cache_path) and not force_cache_reload:
            df = pd.read_pickle(self.cache_path)
            return df
        else:
            print(self.path)
            df = pd.read_csv(self.path, index_col=False, on_bad_lines="skip")
            df.to_pickle(self.cache_path)
            return df


class SensorChannel:
    def __init__(
        self, name, data_path, cache_dir, data_frame_format="sensor", num_channels=1
    ):
        self.files = {}
        self.name = name
        self.ordered_keys = []
        self.file_index = 0
        self.cache_dir = cache_dir
        self.data_path = data_path
        self.active_key = None
        self.active_data = None
        self.active_data_index = 0
        self.data_frame_format = data_frame_format
        self.sensor_type = name
        self.num_channels = num_channels
        self.SENSOR_IGNORE_FIELDS = ["host_epoch_sec", "data_epoch_nsec"]
        self.SENSOR_TIMESTAMP_FIELD = ["data_epoch_nsec"]
        self.GPS_TIMESTAMP_FIELD = ["gps_epoch_sec"]
        self.ACOUSTIC_TIMESTAMP_FIELD = []
        self.ACOUSTIC_CHANNEL_START = None
        self.ACOUSTIC_CHANNEL_STOP = None

    def get_earliest_time(self):
        return self.ordered_keys[0]

    def make_data_frames(self, data):
        output_frames = []
        if self.data_frame_format == "sensor":
            header = list(data.columns.values)
            for ind, line in data.iterrows():
                ts = line[self.SENSOR_TIMESTAMP_FIELD].iloc[0]
                value_dict = {}
                for col in header:
                    if not col in self.SENSOR_IGNORE_FIELDS:
                        value_dict[col] = line[col]
                sensor_timestamp = SensorTimestamp.from_tick(tick_time_int=ts)
                df = DataContainer_Sensor(
                    timestamp=sensor_timestamp,
                    value_dict=value_dict,
                    sensor_type=self.sensor_type,
                )
                output_frames.append(df)
        elif self.data_frame_format == "gps":
            header = list(data.columns.values)
            for ind, line in data.iterrows():
                ts = float(line[self.GPS_TIMESTAMP_FIELD].iloc[0])
                value_dict = {}
                for col in header:
                    if not col in self.GPS_TIMESTAMP_FIELD:
                        value_dict[col] = line[col]
                # print(ts)
                sensor_timestamp = SensorTimestamp.from_unix_time(unix_time_float=ts)

                df = DataContainer_Sensor(
                    timestamp=sensor_timestamp,
                    value_dict=value_dict,
                    sensor_type=self.sensor_type,
                )
                output_frames.append(df)
        elif self.data_frame_format == "acoustic":
            debug_start_t = time.time()

            header = list(data.columns.values)
            if self.ACOUSTIC_CHANNEL_START is None:
                self.ACOUSTIC_CHANNEL_START = header.index("0")
            if self.ACOUSTIC_CHANNEL_STOP is None:
                self.ACOUSTIC_CHANNEL_STOP = (
                    header.index(str(self.num_channels - 1)) + 1
                )
            # USE DIFF TO FIND THE TRANSITIONS?
            packet_transitions = np.concatenate(
                [
                    np.where(np.diff(data["packet_num"]) != 0)[0] + 1,
                    np.array([len(data)]),
                ]
            )
            debug_packet_t = time.time()

            last_end = 0
            num_transitions = len(packet_transitions)
            output_frames = []  # np.empty((num_transitions), dtype="object")
            ind = 0
            debug_max_dt = 0
            debug_slice_t = 0
            while ind < num_transitions:
                end_ind = packet_transitions[ind]
                start_ind = last_end
                packet_num = data["packet_num"].iloc[start_ind]
                tick_time = data["frame_tick_time_nsec"].iloc[start_ind]
                adc_count = data["adc_count"].iloc[start_ind]
                # start_time = np.datetime64(
                #     int(data["packet_epoch_nsec"].iloc[start_ind]), "ns"
                # )
                # print(data["packet_epoch_nsec"].iloc[start_ind] / 1e9)
                start_time = SensorTimestamp.from_unix_time(
                    unix_time_float=float(
                        data["packet_epoch_nsec"].iloc[start_ind] / 1e9
                    )
                )
                start_time.add_tick_time(tick_time_int=int(tick_time), state="PRIMARY")
                debug_slice_start = time.time()

                # doing this slice in two steps seems to be substantially more efficient than as 1 operation
                data_packet_first = data.iloc[
                    slice(start_ind, end_ind),
                    :,
                ]
                data_packet_pd = data_packet_first.iloc[
                    :, slice(self.ACOUSTIC_CHANNEL_START, self.ACOUSTIC_CHANNEL_STOP)
                ]
                debug_slice_end = time.time()

                data_packet = data_packet_pd.transpose().to_numpy(dtype=np.int16)
                debug_slice_t += debug_slice_end - debug_slice_start
                df = DataContainer_Constant_Rate(
                    data=data_packet,
                    sample_rate=52734,
                    start_time=start_time,
                    start_count=adc_count,
                    frame_count=packet_num,
                    tick_time=tick_time,
                )
                # output_frames.append({})
                output_frames.append(df)
                last_end = end_ind
                ind += 1
            debug_end_t = time.time()
            # print("%d, %f" % (ind, debug_end_t - debug_start_t))
            # print(
            #     "Total time %f, per element %f, packet time %f, slice time %f, slice time per element %f"
            #     % (
            #         debug_end_t - debug_start_t,
            #         (debug_end_t - debug_start_t) / ind,
            #         debug_packet_t - debug_start_t,
            #         debug_slice_t,
            #         debug_slice_t / ind,
            #     )
            # )

        return output_frames

    def seek_start(self):
        self.active_data_index = 0
        self.file_index = 0
        try:
            self.active_key = self.ordered_keys[self.file_index]
            self.active_data = self.files[self.active_key]._load_csv_file(False)
        except IndexError:
            self.active_key = None
            self.active_data = None

    def seek_next_file(self):
        print("Seeking")
        print(self.file_index)
        if self.file_index + 1 >= len(self.files.keys()):
            return False
        self.file_index += 1
        self.active_data_index = 0
        self.active_key = self.ordered_keys[self.file_index]
        self.active_data = self.files[self.active_key]._load_csv_file()
        print(self.active_data)

        return True

    def peek_next_time(self):
        if self.active_data_index is None:
            return None
        if self.active_data_index >= len(self.active_data):
            self.seek_next_file()
        return self.active_data["host_epoch_sec"][self.active_data_index]

    def pop_next_sample(self):
        new_data = self.active_data.iloc[self.active_data_index]
        self.active_data_index += 1
        if self.active_data_index >= len(self.active_data):
            self.seek_next_file()
        return new_data

    def pop_up_to_time(self, time):
        samples = []
        # print("pop " + self.name)
        if self.active_data_index >= len(self.active_data):
            print(time)
            self.seek_next_file()
        remaining_frame = self.active_data.iloc[self.active_data_index :]
        # end_index = remaining_frame.loc[remaining_frame["host_epoch_sec"] > time].iat[0]
        end_index = remaining_frame["host_epoch_sec"].searchsorted(time, "left")
        samples = remaining_frame.iloc[0:end_index]
        self.active_data_index += end_index
        # while self.peek_next_time() < time:  # todo handle end case
        #     samples.append(self.pop_next_sample())
        # print(len(samples))
        return samples

    def is_past_end(self, tm):
        return self.active_data.iloc[-2][
            "host_epoch_sec"
        ] < tm and self.file_index == len(
            self.files.keys()
        )  # using 2nd to last. Last line is sometimes mangled

    def add_file(self, fn):
        name = fn.rsplit(".", maxsplit=1)[0]  # remove extension
        st = name.split("_", maxsplit=1)
        if not len(st) == 2:
            return
        prefix = st[0]
        assert prefix == self.name
        ts = st[1]
        file_time = datetime.datetime.strptime(ts, "%Y%m%d-%H%M%S")
        cache_path = os.path.join(self.cache_dir, fn + ".pickle")
        file_path = os.path.join(self.data_path, fn)
        if os.stat(file_path).st_size == 0:
            return  # skip 0 length
        data_file = DataFile(
            filename=fn,
            path=file_path,
            cache_path=cache_path,
            file_time=file_time,
        )
        data = data_file._load_csv_file(force_cache_reload=False)
        data_file.num_samples = len(data)
        if "sample_tick_interp_nsec" in data.columns:
            if len(data["sample_tick_interp_nsec"]) == 0:
                return
            data_file.start_tick = data["sample_tick_interp_nsec"][0]
            data_file.end_tick = data["sample_tick_interp_nsec"].iloc[-1]
        elif "data_epoch_nsec" in data.columns:
            if len(data["data_epoch_nsec"]) == 0:
                return
            data_file.start_tick = data["data_epoch_nsec"][0]
            data_file.end_tick = data["data_epoch_nsec"].iloc[-1]
        if "host_epoch_sec" in data.columns:
            if len(data["host_epoch_sec"]) == 0:
                return
            data_file.host_time_start = data["host_epoch_sec"][0]
            data_file.host_time_end = data["host_epoch_sec"].iloc[-1]
        self.files[data_file.host_time_start] = data_file
        self.ordered_keys = sorted(
            self.files.keys()
        )  # a little inefficient, but probably not worth optimizing


class In_Acsense_CSV_Directory(ABC):
    def __init__(
        self,
        indir,
        cache_dir=None,
        replay_start_time=None,
        channels=None,
        exclude_channels=None,
        num_acoustic_channels=1,
        loop=False,
    ):
        self.indir = indir
        self.data_files = {}
        self.channels = channels
        self.num_acoustic_channels = num_acoustic_channels
        self.exclude_channels = exclude_channels
        self.cache_dir_base = cache_dir
        self.cache_dir = cache_dir
        self.replay_start_time = replay_start_time
        self.replay_time = replay_start_time
        self.clock_time_start = None
        self.loop = loop
        self.loop_any = True  # loop once any channel is past end
        self.callbacks = []
        self.channel_callbacks = {}
        self.paused = False
        self.pause_cmd = False
        self.restart_cmd = False
        self.pause_time = None
        self.new_target_directory = None
        self.load_directory(indir, replay_start_time)
        for chan in self.data_files.keys():
            df = self.data_files[chan]
            discard = df.pop_up_to_time(self.replay_start_time)

        super().__init__()

    def change_directory(self, pth):
        self.new_target_directory = pth

    def load_directory(self, indir, replay_start_time=None):
        self.indir = indir
        self.data_files = {}
        self.data_path = os.path.abspath(indir)
        if self.cache_dir_base is None:
            self.cache_dir = os.path.join(self.data_path, "cache")
        elif os.path.isabs(self.cache_dir_base):
            self.cache_dir = self.cache_dir_base
        else:
            self.cache_dir = os.path.join(self.data_path, self.cache_dir_base)
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        filenames = os.listdir(self.data_path)
        for fn in filenames:
            if not fn.endswith(".csv"):
                continue
            name = fn.rsplit(".", maxsplit=1)[0]  # remove extension
            st = name.split("_", maxsplit=1)
            if not len(st) == 2:
                continue
            prefix = st[0]
            if self.channels is not None:
                if not prefix in self.channels:
                    continue
            if self.exclude_channels is not None:
                if prefix in self.exclude_channels:
                    continue
            ts = st[1]
            if not prefix in self.data_files:
                data_frame_format = "sensor"
                if prefix in ["ACO"]:
                    data_frame_format = "acoustic"
                if prefix in ["GPS"]:
                    data_frame_format = "gps"

                self.data_files[prefix] = SensorChannel(
                    prefix,
                    data_path=self.data_path,
                    cache_dir=self.cache_dir,
                    data_frame_format=data_frame_format,
                    num_channels=self.num_acoustic_channels,
                )
            self.data_files[prefix].add_file(fn)
        # print("Build the cache")
        # self._build_file_cache()
        if replay_start_time is None:
            dts = np.min([d.get_earliest_time() for k, d in self.data_files.items()])
            self.replay_time = dts
            self.replay_start_time = dts
        for k, d in self.data_files.items():
            d.seek_start()

    def restart(self):
        self.restart_cmd = True

    def get_loop_state(self):
        return self.loop

    def enable_loop(self):
        self.loop = True

    def disable_loop(self):
        self.loop = False

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return self.num_channels

    def get_sample_rate(self):
        return self.sample_rate

    def add_callback(self, function):
        self.callbacks.append(function)

    def add_named_callback(self, name, function):
        if not name in self.channel_callbacks:
            self.channel_callbacks[name] = []
        self.channel_callbacks[name].append(function)

    def is_waiting(self):
        return True

    def get_indir(self):
        return self.indir

    def get_replay_time(self):
        return self.replay_time

    def pause(self):
        self.pause_cmd = True

    def resume(self):
        self.pause_cmd = False

    def process(self, end_ts_raw):
        if self.new_target_directory is not None:
            self.load_directory(self.new_target_directory)
            self.new_target_directory = None
        end_ts_int = (
            end_ts_raw - np.datetime64("1970-01-01T00:00:00")
        ) / np.timedelta64(1, "s")
        if self.restart_cmd:
            self.restart_cmd = False
            self.clock_time_start = end_ts_int
            self.replay_time = self.replay_start_time
            for chan in self.data_files.keys():
                self.data_files[chan].seek_start()

            self.paused = False
            self.pause_cmd = False
        if self.paused:
            if not self.pause_cmd:
                total_time_paused = end_ts_raw - self.pause_time
                self.clock_time_start += total_time_paused / np.timedelta64(1, "s")
                self.paused = False
            else:
                return  # remain paused
        else:
            if self.pause_cmd:
                self.paused = True
                self.pause_time = end_ts_raw
            else:
                pass  # continue runnitn normal
        start_t = time.time()

        if self.clock_time_start is None:
            self.clock_time_start = end_ts_int

        end_ts = end_ts_int - self.clock_time_start + self.replay_start_time

        print(end_ts)
        assert end_ts >= self.replay_time
        new_data = {}
        all_done = True
        any_done = False
        for chan in self.data_files.keys():
            df = self.data_files[chan]
            this_done = df.is_past_end(end_ts)
            any_done |= this_done
            all_done &= this_done
            if df.peek_next_time() < self.replay_start_time:
                discard = df.pop_up_to_time(self.replay_start_time)

            new_from_channel = df.pop_up_to_time(end_ts)
            if len(new_from_channel) > 0:
                new_data[chan] = new_from_channel
        if ((self.loop_any and any_done) or all_done) and self.loop:
            self.restart()
            return
        old_replay_time = self.replay_time
        self.replay_time = end_ts
        for chan in new_data.keys():
            sen = self.data_files[chan]
            frames = sen.make_data_frames(new_data[chan])
            for df in frames:
                for cb in self.callbacks:
                    cb(df)
                if chan in self.channel_callbacks.keys():
                    for cb in self.channel_callbacks[chan]:
                        cb(df)
            # print(frames)
        end_t = time.time()
        # print(
        #     "time step processed=%f, elapsed=%f, delta_t process %f"
        #     % (
        #         end_ts - old_replay_time,
        #         end_ts_int - self.clock_time_start,
        #         end_t - start_t,
        #     )
        # )
