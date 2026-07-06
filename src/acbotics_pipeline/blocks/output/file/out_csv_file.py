import csv
import numpy as np
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from acbotics_pipeline.data_containers import DataContainer_Sensor
import time
from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp

import datetime
import os


class Out_CSV_File(PR_Threaded_Process):
    def __init__(
        self,
        filename,
        num_decimals=4,
        max_lines_per_file=None,
        logger_timestamp_column_name="utc_epoch_logger",
        data_timestamp_column_name="utc_epoch_data",
        data_timestamp_column_scale=1,
        start_running=True,
        use_datetime_filenames=False,
    ):
        # probably should be a queue for performance
        self.max_lines_per_file = max_lines_per_file
        self.file_count = 0
        self.logger_timestamp_column_name = logger_timestamp_column_name
        self.data_timestamp_column_name = data_timestamp_column_name
        self.data_timestamp_column_scale = data_timestamp_column_scale
        self.use_datetime_filenames = use_datetime_filenames
        self.running = start_running
        self.outdir = None
        self.current_path = ""
        self.base_filename = filename
        self.file = None
        if not self.base_filename.endswith(".csv"):
            self.base_filename += ".csv"
        if self.running:
            self.start_logging()
        self.num_decimals = num_decimals
        self.lines_written = 0
        super().__init__()

    def set_outdir(self, path):
        self.outdir = path

    def start_logging(self):
        self.current_path = self.get_filename()
        self.file = open(self.current_path, "w", newline="")
        self.csv_writer = csv.writer(
            self.file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        self.running = True

    def stop_logging(self):
        self.running = False
        if self.file:
            try:
                self.file.close()
            except:
                pass
            self.file = None

    def get_filename(self):
        if self.use_datetime_filenames:
            now = datetime.datetime.now()
            dt_str = now.strftime("%Y%m%d-%H%M%S")
            base = self.base_filename.rsplit(".", 1)[0]
            extension = self.base_filename.rsplit(".", 1)[1]
            fn = base + "_" + dt_str + "." + extension
        else:
            if self.max_lines_per_file is None:
                return self.base_filename
            base = self.base_filename.rsplit(".", 1)[0]
            extension = self.base_filename.rsplit(".", 1)[1]
            fn = base + "-" + repr(self.file_count) + "." + extension

        if self.outdir is not None:
            out_path = os.path.join(self.outdir, fn)
        else:
            out_path = fn
        return out_path

    def open_csv(self):
        self.file = open(self.get_filename(), "w", newline="")

        self.csv_writer = csv.writer(
            self.file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

    def get_current_paths(self):
        return [self.current_path]

    def handle_data(self, dc):
        rows = []
        if not self.running:
            return
        if dc.is_constant_rate():
            d = dc.data
            sr = dc.get_sample_rate()
            ts = dc.get_start_time()
            tsf = (ts - np.datetime64(0, "ns")) / np.timedelta64(1, "s")
            t = np.array([[tsf + i / sr for i in range(dc._calculate_data_length())]])
            rows = np.concatenate((t, d), axis=0).transpose()

        elif isinstance(dc, DataContainer_Sensor):
            timestamp = dc.get_timestamps()[0]
            if isinstance(timestamp, SensorTimestamp):
                primary_ticks = timestamp.get_primary_tick_times()
                primary_wall_times = timestamp.get_primary_wall_times()
                if len(primary_ticks) > 0:
                    ts = timestamp.get_tick_time(
                        primary_ticks[0]
                    )  # just take the first
                elif len(primary_wall_times) > 0:
                    ts = timestamp.get_wall_time(
                        primary_wall_times[0]
                    )  # just take the first
                else:
                    ts = 0
            else:
                ts = timestamp
            ts = ts * self.data_timestamp_column_scale
            dic = dc.value_dict
            data = [ts]
            for k in dc.get_csv_header():
                data.append(dic[k])
            rows = np.array([data])

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
            header = [
                self.logger_timestamp_column_name,
                self.data_timestamp_column_name,
            ]
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
