import icontract
import numpy as np
import pylab as plt
from acbotics_pipeline.data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)
from acbotics_pipeline.blocks.output.kivy.out_kivy_plot import Out_Kivy_Plot

from kivy.clock import mainthread


class Out_Kivy_Beamformed_Data(Out_Kivy_Plot):
    def __init__(
        self, update_rate, title="Beamformed Data", ylabel="Signal", color_specs=None
    ):
        # probably should be a queue for performance
        self.unprocessed_data = None
        self.data_buffer = []

        super().__init__(
            update_rate=update_rate,
            title=title,
            xlabel="Angle (deg)",
            ylabel=ylabel,
            color_specs=color_specs,
        )

    def populate_initial_data(self):
        self.graph = plt.plot([0], [0])[0]

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_1D),
        "Must be beamformed data type",
    )
    def input_data(self, dc):
        self.unprocessed_data = dc

    @mainthread
    def kivy_callback(self, dt):
        process_time = self.process_time
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        if self.unprocessed_data is None:
            return

        x = self.unprocessed_data.get_angles() * 360 / (2 * np.pi)
        y = self.unprocessed_data.data

        plt.figure(self.fig)
        self.graph.set_ydata(y)
        self.graph.set_xdata(x)
        self.axes.set_ylim(min(y), max(y))
        self.axes.set_xlim(min(x), max(x))

        plt.draw()
        self.widget.update()
        self.last_update = process_time
