import icontract
import wave
import numpy as np
import os
import struct
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Wav_Detection(PR_Threaded_Process):
    def __init__(self, path, data_type=np.int16):
        # probably should be a queue for performance
        self.unprocessed_data = []
        self.sample_rate = None
        self.data_depth = 0
        self.path = path
        if data_type is np.int16:
            self.data_depth = 16
        elif data_type is np.uint8:
            self.data_depth = 8
        elif data_type is np.int32:
            self.data_depth = 32
        elif data_type is np.float32:
            self.data_depth = 32
        else:
            raise Exception
        super().__init__()

    def __del__(self):
        if self.file:
            self.file.close()
        super().__del__()

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def handle_data(self, dc):
        time_str = repr(
            int(
                (dc.get_start_time() - np.datetime64(0, "ns")) / np.timedelta64(1, "ns")
            )
        )
        for ind in range(dc.data.shape[0]):
            fn = time_str + "-" + repr(ind) + ".wav"
            filename = os.path.join(self.path, fn)
            file = wave.open(filename, "w")

            file.setnchannels(1)
            file.setsampwidth(int(self.data_depth / 8))

            output_data = dc.data[ind, :]
            sample_rate = dc.get_sample_rate()
            file.setframerate(sample_rate)
            file.writeframesraw(output_data.astype(np.int16).tobytes())

    def process(self, t):
        pass
