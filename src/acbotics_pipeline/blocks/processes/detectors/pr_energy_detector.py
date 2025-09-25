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


class Pr_Energy_Detector(Pr_Windowed_Detector):
    def __init__(self, amplitude, window_width, pct_overlap):
        super().__init__(window_width=window_width, pct_overlap=pct_overlap)
        self.amplitude = amplitude

    def detect_on_window(self, data, start_time, sample_rate):
        rms = np.sqrt(np.sum(data.astype(np.float32) ** 2, 1) / data.shape[1])
        # TODO Confirm axis
        detect = rms > self.amplitude
        if max(detect) > 0:
            dc = DataContainer_Detection(
                data=data,
                sample_rate=sample_rate,
                start_time=start_time,
                detection_type="energy",
                detection_score=[d * 10 for d in detect],
            )
            return dc
