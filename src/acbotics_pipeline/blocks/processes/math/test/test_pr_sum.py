import unittest
import time

from blocks.processes.math.pr_sum import Pr_Sum
import numpy as np
from data_containers.data_container_constant_rate import DataContainer_Constant_Rate


class Test_Pr_Sum(unittest.TestCase):
    def setUp(self):
        self.dc = []

    def callback(self, dc):
        self.dc.append(dc)

    def test_pr_sum_maintains_sample_rate(self):
        gain = 5.0
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Sum()
        input = DataContainer_Constant_Rate(
            data=[[1, 3, 5], [2, 4, 6]], sample_rate=sample_rate, start_time=start_time
        )
        block.add_callback(self.callback)
        block.input_data(input)
        while not block.is_waiting():
            pass
        block.process(np.datetime64(time.time_ns(), "ns"))
        self.assertEqual(self.dc[0].get_sample_rate(), sample_rate)
        block.stop_thread()

    def test_pr_sum_maintains_start_time(self):
        gain = 5.0
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Sum()
        input = DataContainer_Constant_Rate(
            data=[[1, 3, 5], [2, 4, 6]], sample_rate=sample_rate, start_time=start_time
        )
        block.add_callback(self.callback)
        block.input_data(input)
        while not block.is_waiting():
            pass
        self.assertEqual(self.dc[0].get_start_time(), start_time)
        block.stop_thread()

    def test_pr_sum_calculation(self):
        gain = 5.0
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Sum()
        input = DataContainer_Constant_Rate(
            data=[[1, 3, 5], [2, 4, 6]], sample_rate=sample_rate, start_time=start_time
        )
        block.add_callback(self.callback)
        block.input_data(input)
        while not block.is_waiting():
            pass
        self.assertEqual(self.dc[0].data[0], 3)
        self.assertEqual(self.dc[0].data[1], 7)
        self.assertEqual(self.dc[0].data[2], 11)
        block.stop_thread()
