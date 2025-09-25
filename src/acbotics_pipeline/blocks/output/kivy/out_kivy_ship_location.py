import icontract
import numpy as np
import pylab as plt

from acbotics_pipeline.blocks.output.kivy.out_kivy_plot import Out_Kivy_Plot

from kivy.clock import mainthread


class Out_Kivy_Ship_Location(Out_Kivy_Plot):
    def __init__(
        self,
        update_rate,
        world,
        title="Ship Locations",
        xmin=-5000,
        xmax=5000,
        ymin=-5000,
        ymax=5000,
        color_specs=None,
        draw_detections=True,
    ):
        # probably should be a queue for performance
        self.world = world
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.draw_detections = draw_detections
        super().__init__(
            update_rate,
            title=title,
            xlabel="X (m)",
            ylabel="Y (m)",
            color_specs=color_specs,
        )
        self.axes.set_xlim((self.xmin, self.xmax))
        self.axes.set_ylim((self.ymin, self.ymax))

    def populate_initial_data(self):
        self.graphs = [
            plt.plot([0, 0], "v")[0],
            plt.plot([0, 0], "o")[0],
            plt.plot([0, 0], "r*")[0],
        ]
        self.detections = [plt.plot([0, 0], "r")[0], plt.plot([0, 0], "r")[0]]

    @mainthread
    def kivy_callback(self, dt):
        process_time = self.process_time
        print("kivy callback" + repr(self.process_time))

        if self.process_time is None:
            return
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            return  # wait before updating

        if not self.paused:
            pass  # TODO

        ships = self.world.ships
        receivers = self.world.receivers
        xs = []
        ys = []
        for name, sh in ships.items():
            if sh.active(process_time):
                xs.append(sh.get_xpos(process_time))
                ys.append(sh.get_ypos(process_time))
        plt.figure(self.fig)
        print(xs)
        print(ys)
        self.graphs[0].set_xdata(xs)
        self.graphs[0].set_ydata(ys)

        xs = []
        ys = []

        for name, rec in receivers.items():
            if rec.active(process_time):
                xs.append(rec.get_xpos(process_time))
                ys.append(rec.get_ypos(process_time))
        self.graphs[1].set_xdata(xs)
        self.graphs[1].set_ydata(ys)

        xs = []
        ys = []
        for name, ping in self.world.pingers.items():
            if ping.active(process_time):
                xs.append(ping.get_xpos(process_time))
                ys.append(ping.get_ypos(process_time))
        self.graphs[2].set_xdata(xs)
        self.graphs[2].set_ydata(ys)

        # if self.draw_detections:
        #     for rec in self.world.receivers:
        #         detections = rec.get_detections_1d()
        #         det = detections[1]
        #         last_det = det[-1]
        #         xval = rec.get_xpos(process_time)
        #         yval = rec.get_ypos(process_time)
        #         i =
        #         for bearing in last_det:
        #             origin = (xval, yval)
        #             big_val = 1000000
        #             print (origin)
        #             print (bearing)
        #             end_pt = (xval + big_val*np.sin(np.radians(bearing)), yval + big_val * np.cos(np.radians(bearing)))
        #         self.detections = [plt.plot([0,0],"r")[0], plt.plot([0,0],'r')[0]]

        print("redrawing")

        plt.draw()
        self.widget.update()
        self.last_update = process_time
