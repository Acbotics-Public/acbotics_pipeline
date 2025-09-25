import icontract
import numpy as np
import pylab as plt
import matplotlib.mlab as mlab
import scipy
import scipy.fft
import math
import queue
from matplotlib.colors import LogNorm


class Out_Pyplot_Spectrogram:
    @icontract.require(
        lambda update_rate: update_rate >= 0, "update_rate must be non negative"
    )
    @icontract.require(lambda title: isinstance(title, str), "title must be string")
    def __init__(
        self,
        update_rate,
        samples_to_use,
        figure_num,
        title="Spectrum Plot",
        num_sigs=1,
        ymin=0.1,
        ymax=1,
    ):
        # probably should be a queue for performance
        self.num_sigs = num_sigs
        self.nfft = 1024
        self.overlap = 512
        self.unprocessed_data = np.array(
            [[0] * samples_to_use for n in range(self.num_sigs)]
        )
        self.update_rate = update_rate
        self.last_update = None
        self.data_buffer = np.array([])
        self.samples_to_use = samples_to_use
        self.figure_num = figure_num
        plt.figure(figure_num)
        self.sample_rate = None
        self.last_frame_number = 0

        [S, f, t] = self.calculate_spectrogram(self.unprocessed_data[0, 0:])
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
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def input_data(self, dc):
        self.sample_rate = dc.get_sample_rate()
        self.unprocessed_data = np.append(self.unprocessed_data, dc.data, 1)
        if not self.last_frame_number + 1 == dc.frame_count:
            print(
                "mismatched frame count in spectrogram. Expected %d, got %d"
                % (self.last_frame_number + 1, dc.frame_count)
            )
        self.last_frame_number = dc.frame_count

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time
        if self.sample_rate is None:
            return
        # if process_time - self.last_update < np.timedelta64(int((1e9)/self.update_rate),'ns'):
        #    return # wait before updating

        self.data_buffer = np.append(self.data_buffer, self.unprocessed_data[0, 0:])
        if len(self.data_buffer) == 0:
            return

        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        while self.data_buffer.shape[0] > 1024:
            d = self.data_buffer[0:1024]
            self.data_buffer = self.data_buffer[1024:]
            [S, f, t] = self.calculate_spectrogram(d)
            curr_im = self.graph.get_array()
            new_im = np.hstack((curr_im, S))
            if new_im.shape[1] > 10 * 4:
                new_im = new_im[:, -100 * 4 :]
            self.graph.set_array(new_im)

        # plt.figure(self.figure_num)

        # TODO slide over window

        # [s,f, t, im] = plt.specgram(self.data_buffer,Fs=self.sample_rate)
        # self.graph.set_data(im.data)
        plt.draw()
