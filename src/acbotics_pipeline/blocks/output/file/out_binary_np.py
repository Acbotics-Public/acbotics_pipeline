import icontract
import csv
import numpy as np
from queue import Queue
from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
import os
import datetime


class Out_Binary_NP(Pr_Multiprocess_Process):
    def __init__(self, basepath, max_files_per_directory=1000, as_process=True):
        subdirs = os.listdir(basepath)
        max_ind = 0
        self.max_files_per_directory = max_files_per_directory
        for d in subdirs:
            try:
                ind = int(d)
                if ind > max_ind:
                    max_ind = ind
            except ValueError:
                pass

        self.base_dir = os.path.join(basepath, str(max_ind + 1))
        if not os.path.exists(self.base_dir):
            os.mkdir(self.base_dir)
        self.file_count = 0
        self.next_dir_ind = 1
        self.active_dir = ""
        self.make_new_subdir()
        self.file_index = 0
        self.data = []
        super().__init__(as_process=as_process)
        # self.thread = threading.Thread(target=self.run_thread)
        # self.thread.start()

    def make_new_subdir(self):
        pth = os.path.join(self.base_dir, str(self.next_dir_ind))
        if not os.path.exists(pth):
            os.mkdir(pth)
        self.next_dir_ind += 1
        self.file_count = 0
        self.active_dir = pth

    # def get_number_of_input_channels(self):
    #    return 1

    # def get_number_of_output_channels(self):
    #    return 0

    # def input_data(self, dc):
    #    self.unprocessed_data.put(dc)

    def __del__(self):
        if self.file:
            self.file.close()

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def handle_data(self, dc):
        # self.data.append(dc.data)
        # if len(self.data) > 20:
        #    n_data = np.concatenate(self.data, axis=1)

        dt_stamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f.dat")
        f = open(os.path.join(self.active_dir, dt_stamp), "wb")
        np.save(f, dc.data)
        f.close()
        self.file_count += 1
        if self.file_count >= self.max_files_per_directory:
            self.make_new_subdir()
        self.file_index += 1
        return None

    def process(self, process_time):
        pass
