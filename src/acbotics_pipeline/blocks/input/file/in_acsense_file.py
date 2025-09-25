from abc import ABC, abstractmethod
import icontract
import numpy as np
import os
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)


class Sense_File_Reader:
    pass


class In_AcSense_File(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(
        self,
        base_path,
        directories=None,
        start_time=np.datetime64(0, "ns"),
        output_batch_size=1,
    ):
        # [self.samplerate, self.data] = scipy.io.wavfile.read(filename)
        self.output_batch_size = output_batch_size
        self.callbacks = []
        self.last_sent_index = 0
        self.start_time = start_time
        if directories is None:
            directories = sorted(os.listdir(base_path))

        self.base_path = base_path
        self.directories = directories
        self.directory = None
        self.file = None
        self.files = []
        self.file_start_time = None
        self.samples_from_file = 0

    def get_next_file(self):
        if len(self.files) == 0:
            if len(self.directories) == 0:
                return False  # Done processing
            self.directory = self.directories.pop(0)
            self.files = sorted(
                os.listdir(os.path.join(self.base_path, self.directory))
            )
        pth = os.path.join(self.base_path, self.directory, self.files.pop(0))
        self.file = open(pth, "rb")
        ts = np.datetime64(int(os.path.getctime(pth) * 1e9), "ns")
        self.file_start_time = ts
        self.samples_from_file = 0
        return True

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return 1

    def get_sample_rate(self):
        return 52768

    def add_callback(self, function):
        self.callbacks.append(function)

    def is_waiting(self):
        return True

    def read_timestamp64(self):
        return int.from_bytes(self.file.read(8), "little")

    def parse_record(self):
        res = {}
        res["timestamp"] = self.read_timestamp64()
        res["dataRecordsPerBuffer"] = int.from_bytes(self.file.read(2), "little")
        res["channels"] = int.from_bytes(self.file.read(1), "little")
        res["bytesPerChannel"] = int.from_bytes(self.file.read(1), "little")
        res["overFlowCount"] = int.from_bytes(self.file.read(2), "little")
        res["firstOverFlowRecord"] = int.from_bytes(self.file.read(2), "little")
        data = [[] for i in range(8)]
        for i in range(255):
            for ch in range(8):
                data[ch].append(
                    int.from_bytes(self.file.read(2), "little", signed=True)
                )
        res["data"] = data
        return res

    def parse_next_record(self):
        ts = None
        if self.file is None:
            self.get_next_file()
        if self.file is None:
            return (ts, [])
        raw_data = [[] for i in range(8)]
        for i in range(50):
            if ts is None:
                ts = self.file_start_time + np.timedelta64(
                    int(1e9 * self.samples_from_file / 52768.0), "ns"
                )
            if self.file.tell() >= os.fstat(self.file.fileno()).st_size:
                res = self.get_next_file()
                if res is False:
                    return None
            block_start = self.file.tell()
            data = self.parse_record()
            self.samples_from_file += 255
            # print(data)
            for i in range(8):
                raw_data[i].extend(data["data"][i])
            self.file.seek(block_start + 0x1000)
        return (ts, raw_data)

    def process(self, process_time):
        (ts, raw_data) = self.parse_next_record()

        dc = DataContainer_Constant_Rate(
            data=raw_data,
            sample_rate=self.get_sample_rate(),
            start_time=ts,
            start_count=0,
        )
        # TODO, fix to update start time by how far first sample is in.

        for c in self.callbacks:
            c(dc)  # I don't think channel should be here. Maybe wrap callback?
