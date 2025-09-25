import unittest

from blocks.output.file.out_csv_file import Out_CSV_File

from data_containers.data_container_constant_rate import DataContainer_Constant_Rate

import numpy as np
import csv
import time


class TestOutCSVFile(unittest.TestCase):
    def setUp(self):
        pass

    def test_out_csv_write_values_correctly(self):
        test_data = np.array([[1, 2, 3, 6, 5, 4, 3, 1]])
        block = Out_CSV_File("test_out.csv")
        start_time = np.datetime64(12345, "ns")
        sample_rate = 44100
        dc = DataContainer_Constant_Rate(test_data, sample_rate, start_time)
        block.input_data(dc)
        block.process(time.time_ns())
        block.stop_thread()
        del block

        with open("test_out.csv", newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",", quotechar="|")
            row_num = 0
            for row in reader:
                self.assertAlmostEqual(
                    float(row[0]),
                    (
                        start_time
                        + np.timedelta64(int(1e9 / sample_rate * row_num), "ns")
                        - np.datetime64(0, "ns")
                    )
                    / np.timedelta64(1, "s"),
                )
                self.assertAlmostEqual(float(row[1]), test_data[0][row_num])
                row_num += 1


if __name__ == "__main__":
    unittest.main()
