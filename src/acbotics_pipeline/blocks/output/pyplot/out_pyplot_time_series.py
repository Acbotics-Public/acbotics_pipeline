import icontract
import numpy as np
import pylab as plt


class Out_Pyplot_Time_Series:
    def __init__(
        self,
        update_rate,
        samples_to_plot,
        figure_num,
        title="Time Series Plot",
        ylabel="Signal",
        ymin=-5,
        ymax=5,
    ):
        # probably should be a queue for performance
        self.unprocessed_data = []
        self.update_rate = update_rate
        self.last_update = None
        self.data_buffer = []
        self.samples_to_plot = samples_to_plot
        self.figure_num = figure_num
        self.ymin = ymin
        self.ymax = ymax
        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("Samples")
        plt.ylabel(ylabel)
        self.graph = plt.plot([0] * samples_to_plot, [0] * samples_to_plot)[0]
        plt.ion()
        self.axes = plt.axes()

    def is_waiting(self):
        return True

    def get_number_of_input_channels(self):
        return 1

    def get_number_of_output_channels(self):
        return 1

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def input_data(self, dc):
        self.unprocessed_data.extend(dc.data)

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        self.data_buffer.extend(self.unprocessed_data)
        if len(self.data_buffer) == 0:
            return

        self.unprocessed_data = []
        self.data_buffer = self.data_buffer[-self.samples_to_plot :]
        x = [x for x in range(0, len(self.data_buffer))]
        y = self.data_buffer

        plt.figure(self.figure_num)
        self.graph.set_ydata(y)
        self.graph.set_xdata(x)
        self.axes.set_ylim(self.ymin, self.ymax)
        self.axes.set_xlim(min(x), max(x))

        plt.draw()
