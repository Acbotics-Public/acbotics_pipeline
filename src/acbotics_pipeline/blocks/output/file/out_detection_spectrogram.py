import icontract
import numpy as np
import os
import struct
import queue

import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


class Out_Detection_Spectrogram:
    def __init__(self, path, nfft=1024, overlap=512, ymin=0.001, ymax=1):
        # probably should be a queue for performance
        self.detections = queue.Queue()
        self.path = path
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        self.nfft = nfft
        self.overlap = overlap
        self.ymin = ymin
        self.ymax = ymax

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
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant spectrogram"
    )
    def input_data(self, dc):
        self.detections.put(dc)

    def is_waiting(self):
        return True

    def process(self, t):
        if not self.detections.empty():
            dc = self.detections.get()
            time_str = repr(
                int(
                    (dc.get_start_time() - np.datetime64(0, "ns"))
                    / np.timedelta64(1, "ns")
                )
            )
            self.sample_rate = dc.get_sample_rate()
            for ind in range(dc.data.shape[0]):
                fn = time_str + "-" + repr(ind) + ".png"
                filename = os.path.join(self.path, fn)

                data = dc.data[ind, :]
                [S, f, t] = self.calculate_spectrogram(data)
                # curr_im = self.graph.get_array()
                # new_im = np.hstack((curr_im,S))
                # if new_im.shape[1] > 10*4:
                #     new_im = new_im[:,-100*4:]
                # self.graph.set_array(new_im)
                extent = (t[0], t[-1] * 4, f[-1], f[0])
                plt.ioff()
                fig = plt.figure()
                print(S.shape)
                self.graph = plt.imshow(
                    S,
                    aspect="auto",
                    extent=extent,
                    interpolation="none",
                    cmap="viridis",
                    norm=LogNorm(vmin=self.ymin, vmax=self.ymax),
                )
                plt.gca().invert_yaxis()
                plt.title(filename + "\n Score = " + repr(int(dc.detection_score[ind])))
                plt.savefig(filename)
                plt.close(fig)
