import pyaudio
import icontract
import struct
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process


class Out_Speaker(PR_Threaded_Process):
    def __init__(self):
        # probably should be a queue for performance
        self.sample_rate = None
        self.audio_out = pyaudio.PyAudio()
        self.stream = None
        super().__init__()

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    @icontract.require(
        lambda self, dc: self.sample_rate is None
        or dc.get_sample_rate() == self.sample_rate,
        "sample_rate must match",
    )
    def handle_data(self, dc):
        if self.stream is None:
            self.initialize_stream(dc.get_sample_rate())
            self.stream.start_stream()
        data = bytes()
        frame_count = dc.data.size
        for i in range(frame_count):
            d = int(dc.data[0][i])
            data = data + struct.pack("h", d)
        self.stream.write(data, frame_count)

    def initialize_stream(self, sample_rate):
        WIDTH = 2
        CHANNELS = 1
        CHUNK = 1024
        self.sample_rate = sample_rate
        self.stream = self.audio_out.open(
            format=self.audio_out.get_format_from_width(WIDTH),
            channels=CHANNELS,
            rate=self.sample_rate,
            input=False,
            output=True,
            frames_per_buffer=CHUNK,
        )

    def __del__(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio_out:
            self.audio_out.terminate()

    def process(self, process_time):
        pass
