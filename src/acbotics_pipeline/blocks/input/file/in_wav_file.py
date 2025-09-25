from abc import ABC, abstractmethod
import icontract
import scipy.io.wavfile
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)


class In_Wav_File(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(self, filename, start_time, output_batch_size=1):
        [self.samplerate, self.data] = scipy.io.wavfile.read(filename)
        self.output_batch_size = output_batch_size
        self.callbacks = []
        self.last_sent_index = 0
        self.start_time = start_time

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return 1

    def get_sample_rate(self):
        return self.file.getframerate()

    def add_callback(self, function):
        self.callbacks.append(function)

    def is_waiting(self):
        return True

    def process(self, process_time):
        end_index = self.last_sent_index + self.output_batch_size
        end_index = min(end_index, len(self.data))
        output_data = np.array(
            [
                self.data[self.last_sent_index : end_index],
            ]
        )
        self.last_sent_index = end_index
        dc = DataContainer_Constant_Rate(
            data=output_data, sample_rate=self.samplerate, start_time=self.start_time
        )
        # TODO, fix to update start time by how far first sample is in.

        for c in self.callbacks:
            c(dc)  # I don't think channel should be here. Maybe wrap callback?
