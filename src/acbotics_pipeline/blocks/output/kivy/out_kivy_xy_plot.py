import icontract
import numpy as np
import numpy as np
import matplotlib

matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")

import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


from gui.kivy.widgets.pyplot_graph import Pyplot_Graph
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

from kivy.clock import mainthread

from acbotics_pipeline.blocks.output.kivy.out_kivy_plot import Out_Kivy_Plot


class Out_Kivy_XY_Plot(Out_Kivy_Plot):
    def __init__(
        self,
        update_rate,
        samples_to_use,
        title="Time Series Plot",
        num_sigs=1,
        xlabel="Samples",
        ylabel="Signal",
        ymin=-5,
        ymax=5,
        color_specs=None,
        auto_scale=False,
    ):
        self.num_sigs = num_sigs
        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])

        self.ymin = ymin
        self.ymax = ymax
        self.sample_rate = None
        self.auto_scale = auto_scale

        self.data_buffer = np.array([[] for n in range(self.num_sigs)])
        self.samples_to_use = samples_to_use

        super().__init__(
            update_rate=update_rate,
            title=title,
            xlabel=xlabel,
            ylabel=ylabel,
            color_specs=color_specs,
        )

    def populate_initial_data(self):
        self.graphs = [
            plt.plot(
                [0] * self.samples_to_use,
                [0] * self.samples_to_use,
                color=self.color_specs["plot_color"],
            )[0]
            for i in range(self.num_sigs)
        ]

    @icontract.require(lambda dc: dc.is_constant_rate(), "sample_rate must be constant")
    def input_data(self, dc):
        self.unprocessed_data = np.append(self.unprocessed_data, dc.data, 1)
        self.sample_rate = dc.get_sample_rate()

    def is_waiting(self):
        return True

    def set_pause(self, p):
        print("setting paused to " + repr(p))
        self.paused = p

    @abstractmethod
    def _calculate_xy_data(self, data):
        pass

    @mainthread
    def kivy_callback(self, dt):
        process_time = self.process_time
        if self.process_time is None:
            return
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        if self.sample_rate is None:
            return

        if not self.paused:
            self.data_buffer = np.append(self.data_buffer, self.unprocessed_data, 1)
            if len(self.data_buffer) == 0:
                return

            self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        self.data_buffer = self.data_buffer[:, -self.samples_to_use :]
        plt.figure(self.fig)

        for i in range(self.num_sigs):
            [x, y] = self._calculate_xy_data(self.data_buffer[i, :])
            self.graphs[i].set_ydata(y)
            self.graphs[i].set_xdata(x)
            if self.auto_scale:
                if len(self.data_buffer[i, :]) > 0:
                    self.axes.set_ylim(min(y), max(y))
                    self.axes.set_xlim(min(x), max(x))
            else:
                if len(self.data_buffer[i, :]) > 0:
                    self.axes.set_ylim(self.ymin, self.ymax)
                    self.axes.set_xlim(min(x), max(x))

        # plt.draw()
        self.widget.update()
        self.last_update = process_time

    def process(self, process_time):
        self.process_time = process_time
