import unittest

import numpy as np
from data_containers.data_container_constant_rate import DataContainer_Constant_Rate


class TestDataContainerConstantRate(unittest.TestCase):
    def test_data_container_constant_rate_is_constant_rate(self):
        d = DataContainer_Constant_Rate(
            data=[], sample_rate=1, start_time=np.datetime64(0, "ns")
        )
        self.assertTrue(d.is_constant_rate())

    def test_data_container_constant_rate_preserves_start_time(self):
        st = np.datetime64(123, "ns")
        d = DataContainer_Constant_Rate(data=[], sample_rate=1, start_time=st)
        self.assertAlmostEqual((d.get_start_time() - st) / np.timedelta64(1, "s"), 0)

    def test_data_container_constant_rate_preserves_sample_rate(self):
        sr = 123.456
        d = DataContainer_Constant_Rate(
            data=[], sample_rate=sr, start_time=np.datetime64(0, "ns")
        )
        self.assertAlmostEqual(d.get_sample_rate(), 123.456)

    def test_data_container_constant_rate_returns_valid_time_series(self):
        sr = 100
        num_samples = 100
        st = np.datetime64(1000121, "ns")
        d = DataContainer_Constant_Rate(
            data=[0] * num_samples, sample_rate=sr, start_time=st
        )
        self.assertEqual(len(d.get_timestamps()), num_samples)
        self.assertEqual(d.get_timestamps()[0], st)
