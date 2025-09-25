import icontract
import numpy as np

from acbotics_pipeline.blocks.output.kivy.out_kivy_xy_plot import Out_Kivy_XY_Plot

import matplotlib

matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")

import matplotlib.pyplot as plt


class Out_Kivy_Time_Series(Out_Kivy_XY_Plot):
    def __init__(
        self,
        update_rate,
        samples_to_plot,
        title="Time Series Plot",
        ylabel="Signal",
        ymin=-5,
        ymax=5,
        num_sigs=1,
        color_specs=None,
        auto_scale=False,
    ):
        super().__init__(
            update_rate=update_rate,
            samples_to_use=samples_to_plot,
            title=title,
            ylabel=ylabel,
            xlabel="time (s)",
            ymin=ymin,
            ymax=ymax,
            num_sigs=num_sigs,
            color_specs=color_specs,
            auto_scale=auto_scale,
        )

    def _calculate_xy_data(self, data):
        x = [x / self.sample_rate for x in range(data.size)]
        y = data
        return [x, y]

    # def populate_initial_data(self):
    #     self.graphs = [plt.plot([0]*self.samples_to_use,[0]*self.samples_to_use, 'r.')[0] for i in range(self.num_sigs)]
