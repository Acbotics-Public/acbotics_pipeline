import icontract
import numpy as np
import pylab as plt
import math
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)

from gui.kivy.widgets.pyplot_graph import Pyplot_Graph

# using app installed version of kivy matplotlib backend
# from backend_kivyagg import FigureCanvasKivyAgg

from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg


from kivy.clock import mainthread

from blocks.output.kivy.out_kivy_beamformed_data_3d import Out_Kivy_Beamformed_Data_3D


class Out_Kivy_Beamformed_Data_3D_With_Ground_Truth(Out_Kivy_Beamformed_Data_3D):
    def __init__(
        self,
        update_rate,
        world,
        receiver_name,
        title="Beamformed Data",
        ylabel="Signal",
        color_specs=None,
    ):
        # probably should be a queue for performance
        self.world = world
        self.receiver_name = receiver_name
        super().__init__(
            update_rate=update_rate,
            title=title,
            ylabel="Elevation (degrees)",
            color_specs=color_specs,
        )

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

        xs = []
        ys = []
        receiver = self.world.receivers[self.receiver_name]
        for name, s in self.world.ships.items():
            if s.active(process_time):
                bearing = (
                    s.get_bearing(receiver, process_time) * 360 / (2 * np.pi) + 360
                ) % 360
                xs.append(bearing)
                elevation = (
                    s.get_elevation(receiver, process_time) * 360 / (2 * np.pi) + 360
                ) % 360
                ys.append(elevation)
        plt.plot(xs, ys, "ro")
        self.widget.update()
