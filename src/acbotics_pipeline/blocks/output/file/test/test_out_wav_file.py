import unittest

from blocks.output.file.out_wav_file import Out_Wav_File
import datetime
import scipy.io.wavfile
import numpy as np
from data_containers.data_container_constant_rate import DataContainer_Constant_Rate
import time


class TestOutWavFile(unittest.TestCase):
    def setUp(self):
        pass

    def test_out_wave_write_zeros_correctly(self):
        test_data = np.zeros((1, 10)).astype(np.int32)
        block = Out_Wav_File("test_out.wav")
        dc = DataContainer_Constant_Rate(
            test_data, sample_rate=44100, start_time=np.datetime64(0, "ns")
        )
        block.input_data(dc)
        while not block.is_waiting():
            pass
        block.stop_thread()
        block.__del__()

        f = scipy.io.wavfile.read("test_out.wav")
        self.assertEqual(f[0], 44100)
        self.assertEqual(f[1][0], 0)

    def test_out_wave_write_values_correctly(self):
        test_data = np.array([[0xB, 0xE, 0xE, 0xF]]).astype(np.int32)

        block = Out_Wav_File("test_out.wav")
        dc = DataContainer_Constant_Rate(
            test_data, sample_rate=44100, start_time=np.datetime64(0, "ns")
        )
        block.input_data(dc)
        while not block.is_waiting():
            pass
        time.sleep(1)
        block.stop_thread()

        block.__del__()
        time.sleep(1)

        f = scipy.io.wavfile.read("test_out.wav")
        self.assertEqual(f[0], 44100)
        self.assertEqual(f[1][0], 0xB)
        self.assertEqual(f[1][3], 0xF)


if __name__ == "__main__":
    unittest.main()
