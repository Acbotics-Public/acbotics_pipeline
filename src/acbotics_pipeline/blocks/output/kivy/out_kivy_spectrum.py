import icontract
import numpy as np

import scipy
import scipy.fft
import math
import time

from kivy.clock import mainthread

from acbotics_pipeline.blocks.output.kivy.out_kivy_xy_plot import Out_Kivy_XY_Plot


class Out_Kivy_Spectrum(Out_Kivy_XY_Plot):
    @icontract.require(
        lambda update_rate: update_rate >= 0, "update_rate must be non negative"
    )
    @icontract.require(lambda title: isinstance(title, str), "title must be string")
    def __init__(
        self,
        update_rate,
        samples_to_use,
        log_y=False,
        title="Spectrum Plot",
        ylabel="Signal",
        ymin=0,
        ymax=5,
        num_sigs=1,
        auto_scale=False,
    ):
        # probably should be a queue for performance
        self.samples_to_use = samples_to_use
        self.log_y = log_y
        self.default_sample_rate = 1000
        super().__init__(
            update_rate=update_rate,
            samples_to_use=samples_to_use,
            title=title,
            xlabel="Frequency (Hz)",
            ylabel=ylabel,
            ymin=ymin,
            ymax=ymax,
            num_sigs=num_sigs,
            auto_scale=auto_scale,
        )

    def calculate_spectrum(self, sig, sample_rate):
        n = len(sig)
        k = scipy.arange(n)
        T = n / sample_rate
        frq = k / T
        frq = frq[range(math.floor(n / 2))]
        Y = scipy.fft.fft(sig) / n
        Y = Y[range(math.floor(n / 2))]
        return (frq, abs(Y))

    def _calculate_xy_data(self, data):
        sample_rate = self.sample_rate
        if sample_rate is None:
            sample_rate = self.default_sample_rate
        [x, y] = self.calculate_spectrum(data, sample_rate)
        if self.log_y:
            y = math.log(y)

        return (x, y)
