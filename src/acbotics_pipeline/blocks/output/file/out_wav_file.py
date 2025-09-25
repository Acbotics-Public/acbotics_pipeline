import icontract
import wave
import numpy as np
import struct
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Wav_File(PR_Threaded_Process):
    def __init__(self, filename_prefix, data_type=np.int16):
        # probably should be a queue for performance
        self.unprocessed_data = []
        self.sample_rate = None
        self.data_depth = 0
        self.file = wave.open(filename_prefix + ".wav", "w")
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

        self.file.setnchannels(1)
        self.file.setsampwidth(int(self.data_depth / 8))
        super().__init__()

    def __del__(self):
        if self.file:
            self.file.close()
        super().__del__()

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def handle_data(self, dc):
        output_data = dc.data[0, :].reshape(-1, 1)
        sample_rate = dc.get_sample_rate()
        if output_data.size == 0:
            self.file.close()
            return

        if self.sample_rate and not self.sample_rate == sample_rate:
            # can't support changing sample rate
            raise Exception()
        elif self.sample_rate is None:
            self.sample_rate = sample_rate
            self.file.setframerate(sample_rate)
        self.file.writeframesraw(output_data.astype(np.int16).tobytes())

    def process(self, t):
        pass
