import icontract
import numpy as np
import math
import pyprctl
import queue
import multiprocessing
from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)


class Pr_Directional_Beamformer(Pr_Multiprocess_Process):
    def __init__(
        self,
        receiver,
        look_angles_deg,
        window_size=1000,
        speed_of_sound=1480,
        as_process=False,
    ):
        """
        Init the block
        receiver: the receiver corresponding to the array + array positions
        look_angles_deg: The angles to beamform to. List of tuples of azimuth and elevation
        window_size: Number of samples to accumulate before running beamforming
        """
        self.receiver = receiver
        self.look_angles_deg = look_angles_deg
        self.window_size = window_size
        self.speed_of_sound = speed_of_sound
        self.start_ind = None
        super().__init__(as_process=as_process)

    def initialize_process(self):
        """
        Initialize variables for windowing the incoming data
        """
        self.unprocessed_data = np.array([])
        self.times = []
        super().initialize_process()

    def calculate_look_delays(self, receiver):
        positions = receiver.get_array_locs(
            xform=False
        )  # may want to use xforms later, but disable for now
        delays = np.zeros((len(self.look_angles_deg), len(positions)))

        for dind in range(len(self.look_angles_deg)):
            direction = self.look_angles_deg[dind]
            azimuth = math.radians(direction[0])
            elevation = math.radians(direction[1])
            for pind in range(len(positions)):
                pos = positions[pind]
                delays[dind, pind] = (
                    pos[0] * np.cos(elevation) * np.cos(azimuth)
                    + pos[1] * np.cos(elevation) * np.sin(azimuth)
                    + pos[2] * np.sin(elevation)
                ) / self.speed_of_sound

        sample_delays = (delays * receiver.sample_rate).astype(np.int32)
        return sample_delays

    def handle_data(self, dc_with_receiver):
        """
        Process incoming data from preceding block. Will accumulate until a full window is reached.
        """
        # print("handling beamform data")
        # If multiprocessing, the receiver must get passed through the queue. Otherwise nav changes won't propogate.
        dc = dc_with_receiver[0]
        receiver = dc_with_receiver[1]
        if not dc.get_sample_rate() == receiver.sample_rate:
            if not self.warned_sample_rate_mismatch:
                print(
                    "Warning. Receiver sample rate does not match data rate. Adjusting to match."
                )
                self.warned_sample_rate_mismatch = True
            receiver.sample_rate = dc.get_sample_rate()

        (timestamps, data) = dc.get_timestamped_data()
        if self.unprocessed_data.size == 0:
            self.unprocessed_data = data
            self.times = timestamps
        else:
            self.unprocessed_data = np.append(self.unprocessed_data, data, 0)
            self.times.extend(timestamps)
        if self.unprocessed_data.size == 0:
            return None
            print("No data to beamform on")
        if self.unprocessed_data.shape[0] > self.window_size:
            # TODO: Calculate beamforming.
            # calculate max delay
            look_delays = self.calculate_look_delays(receiver)
            max_delay = np.max(look_delays)
            min_delay = np.min(look_delays)
            num_channels = self.unprocessed_data.shape[1]
            # determine start index for data
            if self.start_ind is None:
                self.start_ind = max_delay
            # calculate window size that is valid for all channels
            end_ind = (
                self.unprocessed_data.shape[0] - self.start_ind + min_delay
            )  # NOTE min delay will probably be negative
            max_window_size = end_ind - self.start_ind
            # Iterate over look angles
            output = np.zeros((len(look_delays), max_window_size))
            for dind in range(len(look_delays)):
                delays = look_delays[dind]
                # verify length matches number of channels TODO
                for ind in range(len(delays)):
                    output[dind, :] += self.unprocessed_data[
                        self.start_ind
                        - delays[ind] : self.start_ind
                        + max_window_size
                        - delays[ind],
                        ind,
                    ]
                pass  # TODO: check sign of delay

            # rotate data making sure to keep enough for next window

            dc = DataContainer_Constant_Rate(
                data=output / num_channels,
                sample_rate=receiver.sample_rate,
                start_time=self.times[self.start_ind],
            )

            self.unprocessed_data = self.unprocessed_data[max_window_size:]
            self.times = self.times[max_window_size:]

            # handle edge effects
            # At some point: figure out how receiver rotation/motion messes with this.

            return dc
        return None

    def input_data(self, dc):
        """
        Overload super class to pass receiver through along with data container.
        """
        self.waiting = False
        self.dataframes.put((dc, self.receiver))
