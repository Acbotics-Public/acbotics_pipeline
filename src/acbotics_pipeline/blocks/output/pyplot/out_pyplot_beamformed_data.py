import icontract
import numpy as np
import pylab as plt
from acbotics_pipeline.data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)


class Out_Pyplot_Beamformed_Data:
    def __init__(
        self, update_rate, figure_num, title="Beamformed Data", ylabel="Signal"
    ):
        # probably should be a queue for performance
        self.unprocessed_data = None
        self.update_rate = update_rate
        self.last_update = None
        self.data_buffer = []
        self.figure_num = figure_num
        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("Angles (rad)")
        plt.ylabel(ylabel)
        self.graph = plt.plot([0], [0])[0]
        plt.ion()
        self.axes = plt.axes()

    def is_waiting(self):
        return True

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_1D),
        "Must be beamformed data type",
    )
    def input_data(self, dc):
        self.unprocessed_data = dc

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        if self.unprocessed_data is None:
            return

        x = self.unprocessed_data.get_angles()
        y = self.unprocessed_data.data

        plt.figure(self.figure_num)
        self.graph.set_ydata(y)
        self.graph.set_xdata(x)
        self.axes.set_ylim(min(y), max(y))
        self.axes.set_xlim(min(x), max(x))

        plt.draw()
