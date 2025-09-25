import unittest

from blocks.input.generator.in_sine import In_Sine
import numpy as np


class TestInSine(unittest.TestCase):
    def setUp(self):
        self.dc = []

    def callback(self, dc):
        self.dc.append(dc)

    def test_in_sin_has_correct_sample_rate(self):
        start_time = np.datetime64(0, "ns")
        sample_rate = 2000
        block = In_Sine(
            frequency=2000,
            amplitude=3000,
            sample_rate=sample_rate,
            start_time=start_time,
            output_batch_size=10,
        )

        block.add_callback(self.callback)
        block.process(start_time + np.timedelta64(int(10e9), "ns"))
        self.assertEqual(self.dc[0].get_sample_rate(), sample_rate)

    def test_in_sin_is_constant_rate(self):
        start_time = np.datetime64(0, "ns")
        sample_rate = 2000
        block = In_Sine(
            frequency=2000,
            amplitude=3000,
            sample_rate=sample_rate,
            start_time=start_time,
            output_batch_size=10,
        )

        block.add_callback(self.callback)
        block.process(start_time + np.timedelta64(int(10e9), "ns"))
        self.assertTrue(self.dc[0].is_constant_rate())

    def test_in_sin_is_zero_at_zero(self):
        start_time = np.datetime64(0, "ns")
        sample_rate = 2000
        block = In_Sine(
            frequency=8000,
            amplitude=3000,
            sample_rate=sample_rate,
            start_time=start_time,
            output_batch_size=10,
        )

        block.add_callback(self.callback)
        block.process(start_time + np.timedelta64(1, "s"))
        self.assertEqual(self.dc[0].data[0][0], 0)

    def test_in_sin_val_at_pi_4(self):
        start_time = np.datetime64(0, "ns")
        sample_rate = 8000
        block = In_Sine(
            frequency=100,
            amplitude=3000,
            sample_rate=sample_rate,
            start_time=start_time,
            output_batch_size=8000,
        )

        block.add_callback(self.callback)
        block.process(start_time + np.timedelta64(2, "s"))
        self.assertEqual(self.dc[0].data[0][0], 0)


if __name__ == "__main__":
    unittest.main()
