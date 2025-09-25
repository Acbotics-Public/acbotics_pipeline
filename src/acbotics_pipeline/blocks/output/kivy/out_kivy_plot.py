import icontract
import numpy as np
import numpy as np
import matplotlib

matplotlib.use("module://kivy.garden.matplotlib.backend_kivy")

import matplotlib.pyplot as plt
from abc import ABC, abstractmethod


from gui.kivy.widgets.pyplot_graph import Pyplot_Graph

# using app installed version of kivy matplotlib backend
# from backend_kivyagg import FigureCanvasKivyAgg

from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg

from kivy.clock import mainthread


class Out_Kivy_Plot(ABC):
    def __init__(
        self,
        update_rate,
        title="Time Series Plot",
        xlabel="Samples",
        ylabel="Signal",
        color_specs=None,
    ):
        if color_specs is None:
            color_specs = {
                "plot_background": "#343434",
                "axes_background": "#000000",
                "text_color": "#FFFFFF",
                "plot_color": "#0000FF",
                "tick_color": "101010",
            }

        self.color_specs = color_specs
        plt.figure(facecolor=color_specs["plot_background"])
        self.fig = plt.gcf().number
        plt.title(title, color=color_specs["text_color"])
        plt.xlabel(xlabel, color=color_specs["text_color"])
        plt.ylabel(ylabel, color=color_specs["text_color"])
        self.axes = plt.axes()
        self.axes.set_facecolor(color_specs["axes_background"])
        [
            t.set_color(color_specs["tick_color"])
            for t in self.axes.xaxis.get_ticklines()
        ]
        [
            t.set_color(color_specs["tick_color"])
            for t in self.axes.xaxis.get_ticklabels()
        ]
        [
            t.set_color(color_specs["tick_color"])
            for t in self.axes.yaxis.get_ticklines()
        ]
        [
            t.set_color(color_specs["tick_color"])
            for t in self.axes.yaxis.get_ticklabels()
        ]

        self.last_update = None
        self.update_rate = update_rate
        self.process_time = None

        self.populate_initial_data()
        self.paused = False

        self.widget = Pyplot_Graph(plotter=self)

    @abstractmethod
    def populate_initial_data(self):
        pass

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def input_data(self, dc):
        self.unprocessed_data = np.append(self.unprocessed_data, dc.data, 1)
        self.sample_rate = dc.get_sample_rate()

    def is_waiting(self):
        return True

    def set_pause(self, p):
        print("setting paused to " + repr(p))
        self.paused = p

    @abstractmethod
    def kivy_callback(self, dt):
        pass

    def process(self, process_time):
        self.process_time = process_time
