import icontract
import numpy as np
import pylab as plt
import queue


class Out_Pyplot_Detection:
    def __init__(
        self,
        figure_num,
        title="Detection",
        ylabel="Signal",
        num_sigs=1,
        ymin=-5,
        ymax=5,
    ):
        self.detections = queue.Queue()
        self.figure_num = figure_num
        self.ymin = ymin
        self.ymax = ymax
        self.num_sigs = num_sigs
        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("Samples")
        plt.ylabel(ylabel)
        self.graphs = [plt.plot([0], [0])[0] for i in range(num_sigs)]
        plt.ion()
        self.axes = plt.axes()
        self.sample_rate = None

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
        self.detections.put(dc)

    def process(self, process_time):
        if not self.detections.empty():
            dc = self.detections.get()
            if not dc.get_sample_rate() == self.sample_rate:
                self.sample_rate = dc.get_sample_rate()
            for i in range(self.num_sigs):
                d = dc.data[i, :]
                x = [x / self.sample_rate for x in range(0, len(d))]
                self.graphs[i].set_ydata(d)
                self.graphs[i].set_xdata(x)
                if len(d) > 0:
                    self.axes.set_ylim(self.ymin, self.ymax)
                    self.axes.set_xlim(min(x), max(x))
