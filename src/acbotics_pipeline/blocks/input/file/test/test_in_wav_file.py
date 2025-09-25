import unittest

from blocks.input.file.in_wav_file import In_Wav_File
import scipy.io.wavfile
import numpy as np
import time


class TestInWavFile(unittest.TestCase):
    def callback(self, dc):
        self.dc = dc

    def setUp(self):
        self.data = None
        self.time = []

        scipy.io.wavfile.write(
            filename="test.wav", rate=44100, data=np.zeros(10).astype(np.int16)
        )

    def test_in_wav_reads_first_word_correctly(self):
        start_time = np.datetime64(time.time_ns(), "ns")
        filename = "test_zeros.wav"
        block = In_Wav_File(filename, start_time)

        block.add_callback(self.callback)
        block.process(np.datetime64(time.time_ns(), "ns"))
        self.assertEqual(self.dc.data[0], 0)

    def test_in_wav_reads_correct_block_size(self):
        start_time = np.datetime64(time.time_ns(), "ns")
        filename = "test_zeros.wav"
        block = In_Wav_File(filename, start_time, output_batch_size=5)

        block.add_callback(self.callback)
        block.process(np.datetime64(time.time_ns(), "ns"))
        self.assertEqual((self.dc.data.size), 5)


if __name__ == "__main__":
    unittest.main()
