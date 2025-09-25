import icontract
import numpy as np
import copy


class Pr_Delay_Time:
    def __init__(self, delay_sec):
        self.unprocessed_data = []
        self.delay = delay_sec
        self.callbacks = []
        pass

    def get_number_of_input_channels(self):
        return 1

    def get_number_of_output_channels(self):
        return 1

    def input_data(self, dc):
        self.unprocessed_data.append(copy.deepcopy(dc))

    def add_callback(self, function):
        self.callbacks.append(function)

    def process(self, process_time):
        while len(self.unprocessed_data) > 0:
            dc = self.unprocessed_data.pop(0)
            dc.data = dc.data
            dc.start_time = dc.start_time + 1e9 * self.delay
            for c in self.callbacks:
                c(dc)  # I don't think channel should be here. Maybe wrap callback?
