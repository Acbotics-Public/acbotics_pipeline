import icontract
import numpy as np
import pylab as plt


class Out_Pyplot_Ship_Location:
    def __init__(
        self,
        update_rate,
        world,
        figure_num,
        title="Ship Locations",
        xmin=-5000,
        xmax=5000,
        ymin=-5000,
        ymax=5000,
    ):
        # probably should be a queue for performance
        self.update_rate = update_rate
        self.last_update = None
        self.world = world
        self.figure_num = figure_num
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("X (m)")
        plt.ylabel("Y (m)")

        self.graphs = [
            plt.plot([0, 0], "v")[0],
            plt.plot([0, 0], "o")[0],
            plt.plot([0, 0], "r*")[0],
        ]
        plt.ion()
        self.axes = plt.axes()
        self.axes.set_xlim((self.xmin, self.xmax))
        self.axes.set_ylim((self.ymin, self.ymax))

    def is_waiting(self):
        return True

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        ships = self.world.ships
        receivers = self.world.receivers
        xs = []
        ys = []
        for name, sh in ships.items():
            if sh.active(process_time):
                xs.append(sh.get_xpos(process_time))
                ys.append(sh.get_ypos(process_time))
        plt.figure(self.figure_num)
        self.graphs[0].set_xdata(xs)
        self.graphs[0].set_ydata(ys)

        xs = []
        ys = []
        for name, ping in self.world.pingers.items():
            if ping.active(process_time):
                xs.append(ping.get_xpos(process_time))
                ys.append(ping.get_ypos(process_time))
        plt.figure(self.figure_num)
        self.graphs[2].set_xdata(xs)
        self.graphs[2].set_ydata(ys)

        xs = []
        ys = []

        for name, rec in receivers.items():
            if rec.active(process_time):
                xs.append(rec.get_xpos(process_time))
                ys.append(rec.get_ypos(process_time))
        self.graphs[1].set_xdata(xs)
        self.graphs[1].set_ydata(ys)

        plt.draw()
