import icontract
import soundfile as sf
import numpy as np
import struct
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
import datetime


class Out_Audio_File(PR_Threaded_Process):
    @icontract.require(
        lambda format: format.lower() in ["flac", "wav"],
        "supported formats are FLAC, WAV",
    )
    def __init__(
        self, filename_prefix, data_type=np.int16, rollover_min=5, format="wav"
    ):
        # probably should be a queue for performance
        self.unprocessed_data = []
        self.sample_rate = None
        self.data_depth = 0

        self.files = []
        self.ch_per_file = []
        self.filename_prefix = filename_prefix
        self.rollover_min = rollover_min
        self.format = format.lower()

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

        # self.file.setnchannels(1)
        # self.file.setsampwidth(int(self.data_depth / 8))
        super().__init__()

    def __del__(self):
        if self.file:
            self.file.close()
        super().__del__()

    def get_filename(self):
        return (
            self.filename_prefix
            + "_"
            + datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y%m%d-%H%M%S")
            + "."
            + self.format
        )

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def handle_data(self, dc):
        output_data = dc.data
        sample_rate = int(dc.get_sample_rate())

        print(f"Sample rate : {sample_rate}")

        if output_data.size == 0:
            self.file.close()
            return

        if self.sample_rate and not self.sample_rate == sample_rate:
            # can't support changing sample rate
            raise Exception()

        elif self.sample_rate is None:
            self.sample_rate = sample_rate
            # self.file.setframerate(sample_rate)

            # Assume we are using a single output audio file
            num_files = 1
            ch_per_file = np.array([output_data.shape[0]])

            if output_data.shape[0] > 8 and self.format == "flac":
                # FLAC files are restricted to 8ch per file, MAX
                # so if num channels is >8, split into multiple files
                num_files = int(np.ceil(output_data.shape[0] / 8))
                ch_per_file = 8 * np.ones(num_files, dtype=int)
                ch_per_file[-1] = output_data.shape[0] % 8 or 8

            self.ch_per_file = ch_per_file

            filename = self.get_filename()

            for ii in range(num_files):
                self.files.append(
                    sf.SoundFile(
                        (
                            filename
                            if num_files == 1
                            else filename.replace(".", f"_{ii}.")
                        ),
                        mode="w",
                        samplerate=sample_rate,
                        channels=ch_per_file[ii],
                    )
                )

        ch_offset = 0
        for ii, nch in enumerate(self.ch_per_file):
            self.files[ii].write(output_data[ch_offset : ch_offset + nch, :].T)
            ch_offset += nch
            # self.files[ii].flush()
        # self.file.writeframesraw(output_data.astype(np.int16).tobytes())

        if self.files[0].frames >= self.sample_rate * (self.rollover_min * 60):
            filename = self.get_filename()
            num_files = len(self.files)
            for ii in range(num_files):
                self.files[ii].close()
                self.files[ii] = sf.SoundFile(
                    (filename if num_files == 1 else filename.replace(".", f"_{ii}.")),
                    mode="w",
                    samplerate=self.sample_rate,
                    channels=self.ch_per_file[ii],
                )

    def process(self, t):
        pass
