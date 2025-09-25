import icontract
import numpy as np
import pylab as plt
import matplotlib.mlab as mlab
import scipy
import scipy.fft
import math
import queue
from matplotlib.colors import LogNorm


class Out_Pyplot_Detection_Spectrogram:
    @icontract.require(lambda title: isinstance(title, str), "title must be string")
    def __init__(
        self,
        figure_num,
        title="Spectrum Plot",
        nfft=1024,
        overlap=512,
        ymin=0.001,
        ymax=1,
    ):
        # probably should be a queue for performance
        self.nfft = nfft
        self.overlap = overlap
        self.detections = queue.Queue()
        self.figure_num = figure_num
        plt.figure(figure_num)
        self.sample_rate = None
        self.ymin = ymin
        self.ymax = ymax
        [S, f, t] = self.calculate_spectrogram(np.zeros((1, nfft)))
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
        self.title = title
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
        self.detections.put(dc)

    def process(self, process_time):
        if not self.detections.empty():
            dc = self.detections.get()
            best_channel = np.argmax(dc.detection_score)

            data = dc.data[best_channel, :]
            [S, f, t] = self.calculate_spectrogram(data)
            # curr_im = self.graph.get_array()
            # new_im = np.hstack((curr_im,S))
            # if new_im.shape[1] > 10*4:
            #     new_im = new_im[:,-100*4:]
            # self.graph.set_array(new_im)
            extent = (t[0], t[-1] * 4, f[-1], f[0])
            plt.figure(self.figure_num)

            self.graph = plt.imshow(
                S,
                aspect="auto",
                extent=extent,
                interpolation="none",
                cmap="viridis",
                norm=LogNorm(vmin=self.ymin, vmax=self.ymax),
            )
            plt.gca().invert_yaxis()
            plt.title(
                self.title + "\n Score = " + repr(int(dc.detection_score[best_channel]))
            )
            # plt.colorbar() #enable if you want to display a color bar

            # plt.figure(self.figure_num)

            # TODO slide over window

            # [s,f, t, im] = plt.specgram(self.data_buffer,Fs=self.sample_rate)
            # self.graph.set_data(im.data)
            plt.draw()

            plt.ion()
