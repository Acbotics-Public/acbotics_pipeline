import unittest
import time

from blocks.processes.routing.pr_merge import Pr_Merge
import numpy as np
from data_containers.data_container_constant_rate import DataContainer_Constant_Rate


class Test_Pr_Merge(unittest.TestCase):
    def setUp(self):
        self.dc = []

    def callback(self, dc):
        self.dc.append(dc)

    def test_pr_merge_maintains_sample_rate(self):
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Merge(2)
        input1 = DataContainer_Constant_Rate(
            data=[[1, 3, 5]], sample_rate=sample_rate, start_time=start_time
        )
        input2 = DataContainer_Constant_Rate(
            data=[[2, 4, 6]], sample_rate=sample_rate, start_time=start_time
        )

        block.add_callback(self.callback)

        block.get_input_callback(0)(input1)
        block.get_input_callback(1)(input2)
        block.process(np.datetime64(time.time_ns(), "ns"))
        self.assertEqual(self.dc[0].get_sample_rate(), sample_rate)

    def test_pr_merge_maintains_start_time(self):
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Merge(2)
        input1 = DataContainer_Constant_Rate(
            data=[[1, 3, 5]], sample_rate=sample_rate, start_time=start_time
        )
        input2 = DataContainer_Constant_Rate(
            data=[[2, 4, 6]], sample_rate=sample_rate, start_time=start_time
        )

        block.add_callback(self.callback)

        block.get_input_callback(0)(input1)
        block.get_input_callback(1)(input2)
        block.process(np.datetime64(time.time_ns(), "ns"))
        self.assertEqual(self.dc[0].get_start_time(), start_time)

    def test_pr_merge_combines_correctly(self):
        sample_rate = 10
        start_time = np.datetime64(123, "ns")
        block = Pr_Merge(2)
        input1 = DataContainer_Constant_Rate(
            data=[1, 3, 5], sample_rate=sample_rate, start_time=start_time
        )
        input2 = DataContainer_Constant_Rate(
            data=[2, 4, 6], sample_rate=sample_rate, start_time=start_time
        )

        block.add_callback(self.callback)

        block.get_input_callback(0)(input1)
        block.get_input_callback(1)(input2)
        block.process(np.datetime64(time.time_ns(), "ns"))
        self.assertEqual(self.dc[0].data[0, 0], 1)
        self.assertEqual(self.dc[0].data[1, 0], 2)
