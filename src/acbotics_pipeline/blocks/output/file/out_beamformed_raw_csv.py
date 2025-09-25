import icontract
import csv
import numpy as np
import struct
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
import os


class Out_Beamformed_Raw_CSV(PR_Threaded_Process):
    def __init__(self, base_path, prefix, num_decimals=4, max_lines_per_file=None):
        # probably should be a queue for performance
        self.max_lines_per_file = max_lines_per_file
        self.file_count = 0

        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self.prefix = prefix
        self.num_decimals = num_decimals
        self.lines_written = 0
        super().__init__()

    def get_filename(self, ts):
        fn = self.prefix + np.datetime_as_string(ts).replace(":", "_") + ".csv"
        pth = os.path.join(self.base_path, fn)
        return pth

    def open_csv(self, ts):
        self.file = open(self.get_filename(ts), "w", newline="")

        self.csv_writer = csv.writer(
            self.file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

    def handle_data(self, dc):
        self.open_csv(dc.start_time)

        self.csv_writer.writerow(["Frequency", "Theta", "Phi", "Value"])

        rows = []
        # rows.append(dc.frequencies)
        # rows.append(dc.thetas)
        # rows.append(dc.phis)

        for f_ind in range(len(dc.frequencies)):
            for theta_ind in range(len(dc.thetas)):
                for phi_ind in range(len(dc.phis)):
                    freq = dc.frequencies[f_ind]
                    theta = dc.thetas[theta_ind]
                    phi = dc.phis[phi_ind]
                    val = dc.data[theta_ind, phi_ind, f_ind]
                    line = [freq, theta, phi]
                    rows.append([freq, theta, phi, val])
        self.csv_writer.writerows(self._formatdata(rows))
        # self.lines_written += rows.shape[1]
        # start new file
        self.file.close()
        self.file_count += 1
        self.lines_written = 0

    def __del__(self):
        if self.file:
            self.file.close()

    def _formatdata(self, data):
        val_format = "{:.%d}" % (self.num_decimals)
        for row in data:
            res = [row[0]]
            res.extend(
                [val_format.format(row[i]) for i in range(1, len(row))]
            )  # 1 so that we don't format time
            yield res
