import icontract
import numpy as np
import pylab as plt
import scipy
import scipy.fft
import math

from acbotics_pipeline.data_containers.data_container_fft import DataContainer_FFT


class Out_Pyplot_Spectrum_FFT:
    @icontract.require(
        lambda update_rate: update_rate >= 0, "update_rate must be non negative"
    )
    @icontract.require(lambda title: isinstance(title, str), "title must be string")
    def __init__(
        self,
        update_rate,
        figure_num,
        log_y=False,
        title="Spectrum Plot",
        ylabel="Signal",
        ymin=0,
        ymax=5,
        num_sigs=1,
        channels=None,
    ):
        # probably should be a queue for performance
        samples_to_use = 100  # todo. eliminate this
        self.num_sigs = num_sigs
        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        self.update_rate = update_rate
        self.last_update = None
        self.data_buffer = []
        self.channels = channels
        self.figure_num = figure_num

        plt.figure(figure_num)
        self.graphs = [
            plt.plot([0] * samples_to_use, [0] * samples_to_use)[0]
            for i in range(self.num_sigs)
        ]
        plt.title(title)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel(ylabel)

        plt.ion()
        self.log_y = log_y
        self.ymin = ymin
        self.ymax = ymax

    def is_waiting(self):
        return True

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_FFT),
        "Block expects a DataContainer_FFT",
    )
    def input_data(self, dc):
        self.data_buffer = dc.data

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        if len(self.data_buffer) == 0:
            return

        plt.figure(self.figure_num)
        for i in range(self.num_sigs):
            if not self.channels is None and not i in self.channels:
                continue
            n = [n for n in range(0, (self.data_buffer.shape[1]))]
            y = abs(self.data_buffer[i, :])
            x = np.arange(len(y))
            if self.log_y:
                y = np.log10(y)
            self.graphs[i].set_ydata(y)
            self.graphs[i].set_xdata(x)
            # plt.axes().set_xlim(min(x), max(x))
            if len(self.data_buffer[i, :]) > 0:
                self.graphs[i].axes.set_ylim([self.ymin, self.ymax])
                self.graphs[i].axes.set_xlim([min(x), max(x)])

        plt.draw()
