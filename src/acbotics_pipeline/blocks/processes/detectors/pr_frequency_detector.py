import icontract
import numpy as np
import math
import copy
import abc
from acbotics_pipeline.blocks.processes.detectors.pr_windowed_detector import (
    Pr_Windowed_Detector,
)
import arlpy


class Pr_Frequency_Detector(Pr_Windowed_Detector):
    def __init__(self, frequency, amplitude, window_width, pct_overlap):
        super().__init__(window_width=self.window_width, pct_width=self.pct_overlap)
        self.frequency = frequency
        self.amplitude = amplitude

    def detect_on_window(self, data, start_time):
        # perform goetzel
        # compare result to amplitude
        amp = arlpy.signal.goertzel(
            self.frequency, data.data, data.get_sampling_rate, filter=False
        )

        pass
