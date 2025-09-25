from .fixture import Fixture
import threading
import numpy as np
import time
from time import sleep

import matplotlib.pyplot as plt


class Fixture_Pyplot(Fixture):
    def run(self):
        while True:
            t = np.datetime64(time.time_ns(), "ns")
            for b in self.blocks:
                while not b.is_waiting():
                    sleep(0.1)
                b.process(t)
            plt.pause(0.1)
