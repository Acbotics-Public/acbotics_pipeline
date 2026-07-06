import icontract
import numpy as np
import pylab as plt
import matplotlib.mlab as mlab
import scipy
import scipy.fft
import math
import queue
from matplotlib.colors import LogNorm
import copy


class Out_Pyplot_Window:
    @icontract.require(
        lambda update_rate: update_rate >= 0, "update_rate must be non negative"
    )
    @icontract.require(lambda title: isinstance(title, str), "title must be string")
    def __init__(
        self,
        update_rate,
        figure_num,
        title="Window Plot",
        num_sigs=1,
        ymin=0.1,
        ymax=1,
    ):
        # probably should be a queue for performance
        self.num_sigs = num_sigs
        self.nfft = 1024
        self.overlap = 512
        self.unprocessed_data = queue.Queue()
        self.update_rate = update_rate
        self.last_update = None
        self.figure_num = figure_num
        plt.figure(figure_num)
        self.sample_rate = None
        self.last_frame_number = 0

        [S, f, t] = self.calculate_spectrogram([])
        extent = (t[0], t[-1] * 4, f[-1], f[0])
        self.graph = plt.imshow(
            S,
            aspect="auto",
            extent=extent,
            interpolation="none",
            cmap="viridis",
            norm=LogNorm(vmin=ymin, vmax=ymax),
        )
        plt.title(title)
        # plt.xlabel("Time (s)")
        # plt.ylabel("Frequency (Hz)")
        plt.gca().invert_yaxis()
        plt.colorbar()  # enable if you want to display a color bar
        plt.draw()

        plt.ion()

    def is_waiting(self):
        return True

    def calculate_spectrogram(self, data):
        [S, f, t] = mlab.specgram(
            data,
            NFFT=self.nfft,
            Fs=self.sample_rate,
            detrend=None,
            window=None,
            noverlap=self.overlap,
            pad_to=None,
            sides=None,
            scale_by_freq=None,
            mode=None,
        )
        return [S, f, t]

    @icontract.require(
        lambda dc: dc.is_constant_rate(),  # maybe enforce it is a window?
    )
    def input_data(self, dc):
        self.sample_rate = dc.get_sample_rate()
        self.unprocessed_data.put(dc)

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time
        if self.sample_rate is None:
            return
        dc = None
        while self.unprocessed_data.qsize() > 0:
            # we are only consumer
            dc = self.unprocessed_data.get()
        if dc is not None:
            plt.figure(self.figure_num)

            # for i in range(self.num_sigs):
            #     if not self.channels is None and not i in self.channels:
            #         continue
            #     n = [n for n in range(0, (dc.data.shape[1]))]
            #     (x, y) = self.calculate_spectrum(dc.data[i], self.sample_rate)
            #     if self.log_y:
            #         y = np.log10(y)
            #     self.graphs[i].set_ydata(y)
            #     self.graphs[i].set_xdata(x)
            #     # plt.axes().set_xlim(min(x), max(x))
            #     if len(self.data_buffer[i, :]) > 0:
            #         self.graphs[i].axes.set_ylim([self.ymin, self.ymax])
            #         self.graphs[i].axes.set_xlim([min(x), max(x)])
            data_buffer = copy.copy(dc.data[0, :])
            print(data_buffer)
            curr_im = None
            while data_buffer.shape[0] > 1024:
                d = data_buffer[0:1024]
                data_buffer = data_buffer[1024:]
                [S, f, t] = self.calculate_spectrogram(d)
                if curr_im is not None:
                    new_im = np.hstack((curr_im, S))
                else:
                    new_im = S
                if new_im.shape[1] > 10 * 4:
                    new_im = new_im[:, -100 * 4 :]
                curr_im = self.graph.get_array()
                self.graph.set_array(new_im)
                plt.figtext(
                    0.2,
                    0.01,
                    repr(dc.sensors.keys()),
                    wrap=True,
                    horizontalalignment="center",
                    fontsize=10,
                )
        plt.draw()
