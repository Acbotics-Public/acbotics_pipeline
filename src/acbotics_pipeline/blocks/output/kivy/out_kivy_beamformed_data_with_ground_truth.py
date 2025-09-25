import icontract
import numpy as np
import matplotlib.pyplot as plt
from acbotics_pipeline.data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)
from acbotics_pipeline.blocks.output.kivy.out_kivy_beamformed_data import (
    Out_Kivy_Beamformed_Data,
)

from kivy.clock import mainthread


class Out_Kivy_Beamformed_Data_With_Ground_Truth(Out_Kivy_Beamformed_Data):
    def __init__(
        self,
        update_rate,
        world,
        receiver_name,
        title="Beamformed Data With Ground Truth",
        ylabel="Signal",
        color_specs=None,
    ):
        # probably should be a queue for performance
        self.world = world
        self.receiver_name = receiver_name

        super().__init__(
            update_rate=update_rate, title=title, ylabel=ylabel, color_specs=color_specs
        )

    def populate_initial_data(self):
        self.truth = plt.plot([], [], "^g")[0]
        self.detections = plt.plot([], [], "ro")[0]
        super().populate_initial_data()
        self.axes.grid(which="minor", alpha=0.2, axis="x")
        self.axes.grid(which="major", alpha=0.5, axis="x")
        self.axes.set_xticks(np.arange(0, 360, 90))
        self.axes.set_xticks(np.arange(0, 360, 30), minor=True)

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

        xs = []
        receiver = self.world.receivers[self.receiver_name]
        for name, s in self.world.ships.items():
            if s.active(process_time):
                bearing = (
                    s.get_bearing(receiver, process_time) * 360 / (2 * np.pi) + 360
                ) % 360
                xs.append(bearing)

        self.truth.set_xdata(xs)
        self.truth.set_ydata(
            [max(y) - (max(y) - min(y)) * 0.05 for i in range(len(xs))]
        )

        [t, det] = receiver.get_detections_1d()
        xs = []
        if len(det) > 0:
            for a in det[-1]:
                xs.append(a * 360 / (2 * np.pi))
        self.detections.set_xdata(xs)
        self.detections.set_ydata(
            [max(y) - (max(y) - min(y)) * 0.10 for i in range(len(xs))]
        )
        self.axes.set_ylim(min(y), max(y))
        self.axes.set_xlim(min(x), max(x))

        self.widget.update()
        self.last_update = process_time
