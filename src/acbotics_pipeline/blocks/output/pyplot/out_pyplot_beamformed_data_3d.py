import icontract
import numpy as np
import pylab as plt
import math
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)


class Out_Pyplot_Beamformed_Data_3D:
    def __init__(
        self, update_rate, figure_num, title="Beamformed Data", ylabel="Signal"
    ):
        # probably should be a queue for performance
        self.unprocessed_data = None
        self.update_rate = update_rate
        self.last_update = None
        self.data_buffer = []
        self.figure_num = figure_num
        plt.figure(figure_num)
        plt.title(title)
        plt.xlabel("Bearing (degrees)")
        plt.ylabel("Elevation (degrees)")
        self.graph = plt.plot([0], [0])[0]
        plt.ion()
        self.axes = plt.axes()

    def is_waiting(self):
        return True

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_2D),
        "Must be beamformed data type",
    )
    def input_data(self, dc):
        self.unprocessed_data = dc

    def process(self, process_time):
        if self.last_update is None:
            self.last_update = process_time

        if process_time - self.last_update < np.timedelta64(
            int((1e9) / self.update_rate), "ns"
        ):
            print("waiting to update")
            return  # wait before updating

        if self.unprocessed_data is None:
            print("No Data")
            return
        thetas = self.unprocessed_data.get_thetas()
        phis = self.unprocessed_data.get_phis()
        y = self.unprocessed_data.data

        plt.figure(self.figure_num)

        plt.clf()
        # plt.pcolor(np.array(thetas)*180/math.pi,np.array(phis)*180/math.pi,self.unprocessed_data.data)
        phi_mesh, theta_mesh = np.meshgrid(phis, thetas)

        plt.pcolor(
            theta_mesh * 180 / math.pi,
            phi_mesh * 180 / math.pi,
            self.unprocessed_data.data,
        )

        # plt.plot(ship_bearing[ind]*180/math.pi,ship_elevation[ind]*180/math.pi,'bo')
        # plt.plot(list_output[:,0]*180/math.pi,list_output[:,1]*180/math.pi,'ro')
        # plt.legend(['true bearing/elevation','possible bearing/elevation','beamforming matrix',])
        plt.xlabel("Bearing (degrees)")
        plt.ylabel("Elevation (degrees)")

        plt.title(repr(self.unprocessed_data.start_time))

        # plt.pause(0.1)

        # self.graph.set_ydata(y)
        # self.graph.set_xdata(x)
        # self.axes.set_ylim(min(y), max(y))
        # self.axes.set_xlim(min(x), max(x))
        self.last_update = process_time

        plt.draw()
