import icontract
import numpy as np
import pylab as plt
from acbotics_pipeline.data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)

import queue


class Out_Pyplot_Beamformed_Waterfall:
    def __init__(
        self,
        update_rate,
        figure_num,
        max_time_len=1 * 6000,
        title="Beamformed Data",
        ylabel="Signal",
        color_specs=None,
    ):
        # probably should be a queue for performance
        self.unprocessed_data = queue.Queue()
        self.data_buffer = []
        self.max_time_len = max_time_len
        self.beamformed_1ds = []
        self.angles = []
        self.times = []
        self.init_time = None
        self.figure_num = figure_num
        self.update_rate = update_rate
        self.title = title
        self.xlabel = "Angle (deg)"
        self.ylabel = ylabel
        self.graph = plt.plot([0], [0])[0]
        self.last_update = None

    def is_waiting(self):
        return True

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_1D),
        "Must be beamformed data type",
    )
    def input_data(self, dc):
        self.unprocessed_data.put(dc)

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        if self.unprocessed_data is None:
            return

        while not self.unprocessed_data.empty():
            dc = self.unprocessed_data.get()
            self.beamformed_1ds.append(dc.data / np.max(dc.data))
            if len(self.angles) == 0:
                self.angles = dc.angles
            if self.init_time is None:
                self.init_time = dc.get_start_time()
            self.times.append(dc.get_start_time())

        if len(self.times) == 0:
            print("No Times")
            return
        t_start_index = 0
        while True:
            if self.times[-1] - self.times[t_start_index] <= np.timedelta64(
                self.max_time_len, "s"
            ):
                break
            print("incrementing t_start_index")
            t_start_index += 1
            if t_start_index >= len(self.times):
                print("Ran out of Times")
                return
        print("t_start index= " + repr(t_start_index))
        self.times = self.times[t_start_index:]
        self.beamformed_1ds = self.beamformed_1ds[t_start_index:]

        plt.figure(self.figure_num)
        times = (self.times - self.times[0]) / np.timedelta64(1, "s")
        plt.clf()
        plt.pcolor(
            self.angles * 360 / (2 * np.pi),
            times,
            20 * np.log10(np.abs(np.array(self.beamformed_1ds))),
        )
        # plt.clim(vmin=-30,vmax=-70)
        # plt.plot(times,max_ang*180/math.pi,'rx',times,true_ang*180/math.pi,'g-')
        plt.ylabel("time (s)")
        plt.xlabel("bearing (deg)")
        plt.colorbar()

        self.last_update = process_time
