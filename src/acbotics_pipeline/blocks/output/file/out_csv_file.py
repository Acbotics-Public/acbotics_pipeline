import csv
import numpy as np
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process

import time


class Out_CSV_File(PR_Threaded_Process):
    def __init__(self, filename, num_decimals=4, max_lines_per_file=None):
        # probably should be a queue for performance
        self.max_lines_per_file = max_lines_per_file
        self.file_count = 0

        self.base_filename = filename + ".csv"
        self.file = open(self.get_filename(), "w", newline="")
        self.csv_writer = csv.writer(
            self.file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        self.num_decimals = num_decimals
        self.lines_written = 0
        super().__init__()

    def get_filename(self):
        if self.max_lines_per_file is None:
            return self.base_filename
        base = self.base_filename.rsplit(".", 1)[0]
        extension = self.base_filename.rsplit(".", 1)[1]
        return base + "-" + repr(self.file_count) + "." + extension

    def open_csv(self):
        self.file = open(self.get_filename(), "w", newline="")

        self.csv_writer = csv.writer(
            self.file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

    def handle_data(self, dc):
        rows = []

        if dc.is_constant_rate():
            d = dc.data
            sr = dc.get_sample_rate()
            ts = dc.get_start_time()
            tsf = (ts - np.datetime64(0, "ns")) / np.timedelta64(1, "s")
            t = np.array([[tsf + i / sr for i in range(dc._calculate_data_length())]])
            rows = np.concatenate((t, d), axis=0).transpose()

        else:
            for data in zip(dc.get_timestamped_data()[0], dc.get_timestamped_data()[1]):
                t = (data[0] - np.datetime64(0, "ns")) / np.timedelta64(1, "s")
                d = data[1]
                v = [t]
                v.extend(d)
                rows.append(v)

            rows = np.array(rows)

        if self.lines_written == 0 and dc.get_csv_header() is not None:
            # write header
            header = ["utc_epoch_logger", "utc_epoch_data"]
            header.extend(dc.get_csv_header())
            print(header)
            self.csv_writer.writerow(header)

        self.csv_writer.writerows(self._formatdata(rows))
        self.lines_written += rows.shape[1]
        self.file.flush()
        # start new file
        if (
            self.max_lines_per_file is not None
            and self.lines_written >= self.max_lines_per_file
        ):
            # self.csv_writer.close()
            self.file.close()
            self.file_count += 1
            self.lines_written = 0
            self.open_csv()

    def __del__(self):
        if self.file:
            self.file.close()

    def _formatdata(self, data):

        # we probably don't want to write scientific notation here;
        # this lambda will force self.num_decimals, then trim trailing zeros;
        # if result is an integer, it will remove the decimal point as well
        format_val = lambda x: (
            ("{:.%df}" % self.num_decimals).format(x).rstrip("0").rstrip(".")
        )

        # use a single logger timestamp for a given block
        # (ie all audio frames in a single constant-rate UDP packet)
        log_ts = time.time_ns() / 1e9

        for row in data:
            res = [log_ts, row[0]]
            # iterate from index:1 so that we don't format time;
            # expect time to have more decimals than self.num_decimals
            res.extend([format_val(row[i]) for i in range(1, len(row))])
            yield res
