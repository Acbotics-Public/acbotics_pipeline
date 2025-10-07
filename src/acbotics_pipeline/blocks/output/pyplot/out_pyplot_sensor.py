import icontract
import numpy as np
import pylab as plt
import queue
from collections import deque


class Out_Pyplot_Sensor:
    def __init__(
        self,
        update_rate,
        samples_to_plot,
        figure_num,
        title="Sensor Plot",
        ylabel="Signal",
        ymin=-5,
        ymax=5,
        num_sigs=1,
        channels=None,
    ):
        self.num_sigs = num_sigs
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
        self.data_buffer = {"timestamp": deque(maxlen=self.samples_to_plot)}
        self.title = title
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

    def is_waiting(self):
        return True

    def input_data(self, dc):
        self.received_data.put(dc)

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating
        while not self.received_data.empty():
            # while self.received_data.qsize() > 100: # hack to handle too muxh data
            #     self.received_data.get()
            data = self.received_data.get()
            for k in data.value_dict.keys():
                if not k in self.data_buffer.keys():
                    self.data_buffer[k] = deque(
                        [0 for i in range(len(self.data_buffer["timestamp"]))],
                        maxlen=self.samples_to_plot,
                    )
                self.data_buffer[k] += deque([data.value_dict[k]])
            self.data_buffer["timestamp"] += deque([data.timestamp])

        plt.figure(self.figure_num)
        plt.cla()
        labels = []
        for k in self.data_buffer.keys():
            if k is "timestamp":
                continue
            plt.plot(
                np.array(self.data_buffer["timestamp"]), np.array(self.data_buffer[k])
            )
            labels.append(k)
        plt.legend(labels)
        plt.title(self.title)
        plt.draw()
