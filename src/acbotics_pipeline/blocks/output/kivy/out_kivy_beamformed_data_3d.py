import icontract
import numpy as np
import pylab as plt
import math
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)

from gui.kivy.widgets.pyplot_graph import Pyplot_Graph
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.clock import mainthread

from acbotics_pipeline.blocks.output.kivy.out_kivy_plot import Out_Kivy_Plot


class Out_Kivy_Beamformed_Data_3D(Out_Kivy_Plot):
    def __init__(
        self, update_rate, title="Beamformed Data", ylabel="Signal", color_specs=None
    ):
        # probably should be a queue for performance
        self.unprocessed_data = None
        self.update_rate = update_rate
        self.last_update = None
        self.data_buffer = []
        super().__init__(
            update_rate=update_rate,
            title=title,
            xlabel="Bearing (degrees)",
            ylabel="Elevation (degrees)",
            color_specs=color_specs,
        )

    def populate_initial_data(self):
        self.graph = plt.plot([0], [0])[0]

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_2D),
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

        thetas = self.unprocessed_data.get_thetas()
        phis = self.unprocessed_data.get_phis()
        y = self.unprocessed_data.data

        plt.figure(self.fig)

        plt.clf()
        phi_mesh, theta_mesh = np.meshgrid(phis, thetas)

        plt.pcolor(
            theta_mesh * 180 / math.pi,
            phi_mesh * 180 / math.pi,
            self.unprocessed_data.data,
        )
        plt.xlabel("Bearing (degrees)")
        plt.ylabel("Elevation (degrees)")

        self.widget.update()
