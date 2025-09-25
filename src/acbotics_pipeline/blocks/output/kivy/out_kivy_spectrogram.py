import icontract
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# matplotlib.use('module://backend_kivy')

import matplotlib.mlab as mlab
import scipy
import scipy.fft
import math
from matplotlib.colors import LogNorm

from gui.kivy.widgets.pyplot_graph import Pyplot_Graph
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.clock import mainthread

from acbotics_pipeline.blocks.output.kivy.out_kivy_plot import Out_Kivy_Plot


class Out_Kivy_Spectrogram(Out_Kivy_Plot):
    @icontract.require(
        lambda update_rate: update_rate >= 0, "update_rate must be non negative"
    )
    @icontract.require(lambda title: isinstance(title, str), "title must be string")
    def __init__(
        self,
        update_rate,
        samples_to_use,
        title="Spectrogram Plot",
        num_sigs=1,
        ymin=0.1,
        ymax=1,
        color_specs=None,
    ):
        # probably should be a queue for performance
        self.num_sigs = num_sigs
        self.nfft = 1024
        self.overlap = 512
        self.ymin = ymin
        self.ymax = ymax
        self.unprocessed_data = np.array(
            [[0] * samples_to_use for n in range(self.num_sigs)]
        )
        self.data_buffer = np.array([])
        self.samples_to_use = samples_to_use
        self.sample_rate = None

        # plt.xlabel("Time (s)")
        # plt.ylabel("Frequency (Hz)")
        super().__init__(
            update_rate=update_rate,
            title=title,
            xlabel="Time (s)",
            ylabel="Frequency (Hz)",
            color_specs=color_specs,
        )
        plt.gca().invert_yaxis()
        plt.colorbar()  # enable if you want to display a color bar
        # plt.draw()

    def populate_initial_data(self):
        [S, f, t] = self.calculate_spectrogram(self.unprocessed_data[0, 0:])
        extent = (t[0], t[-1] * 4, f[-1], f[0])
        print(S)
        self.graph = plt.imshow(
            S,
            aspect="auto",
            extent=extent,
            interpolation="none",
            cmap="viridis",
            norm=LogNorm(vmin=self.ymin, vmax=self.ymax),
        )

    def is_waiting(self):
        return True

    def calculate_spectrogram(self, data):
        [S, f, t] = mlab.specgram(
            data,
            NFFT=self.nfft,
            Fs=self.sample_rate,
            detrend=None,
            window=None,
            noverlap=None,
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

    @mainthread
    def kivy_callback(self, dt):
        pass
        if self.sample_rate is None:
            return
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
        self.widget.update()
