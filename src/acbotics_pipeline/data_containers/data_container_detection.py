from abc import ABC, abstractmethod
import icontract
from .data_container_constant_rate import DataContainer_Constant_Rate
import numpy as np
import math


class DataContainer_Detection(DataContainer_Constant_Rate):
    def __init__(
        self,
        data,
        sample_rate,
        start_time,
        detection_type,
        detection_score,
        frame_count=None,
    ):
        self.detection_type = detection_type
        self.detection_score = detection_score
        super().__init__(data, sample_rate, start_time, frame_count)
