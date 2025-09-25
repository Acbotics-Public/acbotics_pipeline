import icontract
import numpy as np
import pylab as plt
import queue


class Out_Pyplot_Energy_Bar_Plot:
    def __init__(
        self,
        update_rate,
        samples_to_use,
        figure_num,
        title="Energy",
        ylabel="Signal",
        num_sigs=1,
        ymin=-5,
        ymax=5,
    ):
        self.update_rate = update_rate
        self.samples_to_use = samples_to_use
        self.figure_num = figure_num
        self.last_update = None
        self.ymin = ymin
        self.ymax = ymax
        self.num_sigs = num_sigs
        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("Samples")
        plt.ylabel(ylabel)
        self.graph = plt.bar(np.ones(num_sigs), np.ones(num_sigs))[0]
        plt.ion()
        # self.axes = plt.axes()
        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        self.data_buffer = np.array([[] for n in range(self.num_sigs)])

    def is_waiting(self):
        return True

    def get_number_of_input_channels(self):
        return 1

    def get_number_of_output_channels(self):
        return 1

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def input_data(self, dc):
        print("DATA")
        self.unprocessed_data = np.append(self.unprocessed_data, dc.data, 1)
        self.sample_rate = dc.get_sample_rate()

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating
        self.data_buffer = np.append(self.data_buffer, self.unprocessed_data, 1)
        if len(self.data_buffer) == 0:
            return
        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        self.data_buffer = self.data_buffer[:, -self.samples_to_use :]

        d = self.data_buffer
        rms = np.sqrt(np.sum(d.astype(np.float32) ** 2, 1) / d.shape[1])
        # self.graph.set_ydata(rms)
        plt.figure(self.figure_num)
        plt.clf()
        self.graph = plt.bar(np.arange(0, len(rms)), rms)
        print("PLOTTING")
        # if len(d) > 0:
        #    self.axes.set_ylim(self.ymin,self.ymax)
