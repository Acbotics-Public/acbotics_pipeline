import unittest
import time

from blocks.processes.math.pr_gain import Pr_Gain
import numpy as np
from data_containers.data_container_constant_rate import DataContainer_Constant_Rate


class TestPRGain(unittest.TestCase):
    def setUp(self):
        self.dc = []

    def callback(self, dc):
        self.dc.append(dc)

    def test_pr_gain_maintains_sample_rate(self):
        gain = 5.0
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Gain(gain)
        input = DataContainer_Constant_Rate(
            data=[1, 2, 3], sample_rate=sample_rate, start_time=start_time
        )
        block.add_callback(self.callback)
        block.input_data(input)
        while not block.is_waiting():
            pass
        block.stop_thread()
        self.assertEqual(self.dc[0].get_sample_rate(), sample_rate)

    def test_pr_gain_maintains_start_time(self):
        gain = 5.0
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Gain(gain)
        input = DataContainer_Constant_Rate(
            data=[1, 2, 3], sample_rate=sample_rate, start_time=start_time
        )
        block.add_callback(self.callback)
        block.input_data(input)
        while not block.is_waiting():
            pass
        block.stop_thread()
        self.assertEqual(
            (self.dc[0].get_start_time() - start_time) / np.timedelta64(1, "s"), 0
        )

    def test_pr_gain_calculation(self):
        gain = 5.0
        sample_rate = 10
        start_time = np.datetime64(123, "s")
        block = Pr_Gain(gain)
        input = DataContainer_Constant_Rate(
            data=[1, 2, 3], sample_rate=sample_rate, start_time=start_time
        )
        block.add_callback(self.callback)
        block.input_data(input)
        while not block.is_waiting():
            pass
        block.stop_thread()
        self.assertEqual(self.dc[0].data[0][0], 5)
        self.assertEqual(self.dc[0].data[0][1], 10)
        self.assertEqual(self.dc[0].data[0][2], 15)
