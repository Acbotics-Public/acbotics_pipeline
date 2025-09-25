import icontract
import numpy as np
import pylab as plt
import queue


class Out_Pyplot_Time_Series_Multiple:
    def __init__(
        self,
        update_rate,
        samples_to_plot,
        figure_num,
        title="Time Series Plot",
        ylabel="Signal",
        ymin=-5,
        ymax=5,
        num_sigs=1,
        channels=None,
    ):
        # probably should be a queue for performance
        self.num_sigs = num_sigs
        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        self.received_data = queue.Queue()
        self.update_rate = update_rate
        self.last_update = None
        self.samples_to_plot = samples_to_plot
        self.figure_num = figure_num
        self.ymin = ymin
        self.ymax = ymax
        self.channels = channels
        if not channels is None:
            self.num_plots = len(channels)
        else:
            self.num_plots = num_sigs
            self.channels = [i for i in range(num_sigs)]
        self.data_buffer = np.array([[] for n in range(self.num_sigs)])

        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("Time (s)")
        plt.ylabel(ylabel)
        self.graphs = [
            plt.plot(np.arange(samples_to_plot), [0] * samples_to_plot)[0]
            for i in range(self.num_plots)
        ]
        plt.ion()
        # self.axes = plt.axes()
        self.sample_rate = None

    def is_waiting(self):
        return True

    @icontract.require(lambda dc: dc.is_constant_rate(), "sample_rate must be constant")
    def input_data(self, dc):
        self.received_data.put(dc.data)
        # self.unprocessed_data = np.append(self.unprocessed_data, dc.data,1)
        self.sample_rate = dc.get_sample_rate()

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating
        new_data = []
        if self.unprocessed_data.size > 0:
            new_data.append(self.unprocessed_data)
        while not self.received_data.empty():
            # while self.received_data.qsize() > 100: # hack to handle too muxh data
            #     self.received_data.get()
            new_data.append(self.received_data.get())
        if len(new_data) > 0:
            self.unprocessed_data = np.concatenate(new_data, axis=1)
        self.data_buffer = np.append(self.data_buffer, self.unprocessed_data, 1)
        if len(self.data_buffer) == 0:
            return

        self.unprocessed_data = np.array([[] for n in range(self.num_sigs)])
        self.data_buffer = self.data_buffer[:, -self.samples_to_plot :]
        plt.figure(self.figure_num)
        for i in range(self.num_plots):
            x = [x / self.sample_rate for x in range(0, (self.data_buffer.shape[1]))]
            self.graphs[i].set_ydata(self.data_buffer[self.channels[i], :])
            self.graphs[i].set_xdata(x)
            if len(self.data_buffer[i, :]) > 0:
                self.graphs[i].axes.set_ylim([self.ymin, self.ymax])
                self.graphs[i].axes.set_xlim([min(x), max(x)])

        plt.draw()
