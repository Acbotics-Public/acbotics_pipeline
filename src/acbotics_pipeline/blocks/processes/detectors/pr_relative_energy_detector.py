import icontract
import numpy as np
import math
import copy
import abc
from acbotics_pipeline.blocks.processes.detectors.pr_windowed_detector import (
    Pr_Windowed_Detector,
)
from acbotics_pipeline.data_containers.data_container_detection import (
    DataContainer_Detection,
)


class Pr_Relative_Energy_Detector(Pr_Windowed_Detector):
    def __init__(self, amplitude, window_width, pct_overlap, base_windows):
        super().__init__(window_width=window_width, pct_overlap=pct_overlap)
        self.amplitude = amplitude
        self.base_windows = base_windows
        self.base_rms = []

    def detect_on_window(self, data, start_time, sample_rate):
        rms = np.sqrt(np.sum(data.astype(np.float32) ** 2, 1) / data.shape[1])
        if len(self.base_rms) < self.base_windows:
            self.base_rms.append(rms)
        else:
            # TODO Confirm axis
            base_rms = np.zeros(self.base_rms[0].shape)

            for br in self.base_rms:
                base_rms += br

            detect = rms / br > self.amplitude

            # rotate the base values
            self.base_rms.pop(0)
            self.base_rms.append(rms)
            print(max(rms / br))
            if max(detect) > 0:
                dc = DataContainer_Detection(
                    data=data,
                    sample_rate=sample_rate,
                    start_time=start_time,
                    detection_type="energy",
                    detection_score=(rms / br) / self.amplitude,
                )
                print("detect")
                return dc
