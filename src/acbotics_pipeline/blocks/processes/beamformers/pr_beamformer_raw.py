import icontract
import numpy as np
import math
import pyprctl
import queue
import multiprocessing
from blocks.base.pr_multiprocess_process import Pr_Multiprocess_Process
from data_containers.data_container_beamformed_output_raw import (
    DataContainer_Beamformed_Output_Raw,
)
import time
import acbeamform
import acbeamform_old


class Pr_Beamformer_Raw(Pr_Multiprocess_Process):
    def __init__(self, receiver, bf_config, as_process=True):
        """
        Init the block
        receiver: the receiver corresponding to the array + array positions
        bf_config: The beamformer configuration
        """
        self.receiver = receiver
        self.bf_config = bf_config
        self.warned_sample_rate_mismatch = False
        self.BF_obj = acbeamform.AcBeamformed.from_receiver_and_acbeamconfig(
            receiver=receiver, bf_config=self.bf_config, verbose=1
        )
        super().__init__(as_process=as_process)

    def initialize_process(self):
        """
        Initialize variables for windowing the incoming data
        """
        window_size = self.bf_config["BF_window_length_s"] * self.receiver.sample_rate
        num_channels = len(self.receiver.array_config["array_x"])
        self.unprocessed_data = np.zeros((window_size, num_channels))
        self.unprocessed_data_ind = 0
        self.times = np.array(
            [np.datetime64(0, "ns") for i in range(window_size)], dtype="datetime64"
        )
        super().initialize_process()

    def handle_data(self, dc_with_receiver):
        """
        Process incoming data from preceding block. Will accumulate until a full window is reached.
        """
        # print("handling beamform data")
        # If multiprocessing, the receiver must get passed through the queue. Otherwise nav changes won't propogate.
        start_t = time.time()
        dc = dc_with_receiver[0]
        receiver = dc_with_receiver[1]
        if not dc.get_sample_rate() == receiver.sample_rate:
            if not self.warned_sample_rate_mismatch:
                print(
                    "Warning. Receiver sample rate does not match data rate. Adjusting to match."
                )
                self.warned_sample_rate_mismatch = True
            receiver.sample_rate = dc.get_sample_rate()
        window_size = self.bf_config["BF_window_length_s"] * receiver.sample_rate

        (timestamps, data) = dc.get_timestamped_data()
        # print(dc.start_time)
        # print(timestamps)
        num_samples = data.shape[0]
        # print("data prep time: " + repr(time.time()-start_t))
        # print(self.unprocessed_data.shape)
        # print(data.shape)
        if self.unprocessed_data_ind + num_samples < self.unprocessed_data.shape[0]:
            # can add all of data to buffer
            self.unprocessed_data[
                self.unprocessed_data_ind : self.unprocessed_data_ind + num_samples, :
            ] = data
            # print(self.times)
            self.times[
                self.unprocessed_data_ind : self.unprocessed_data_ind + num_samples
            ] = timestamps

            self.unprocessed_data_ind += num_samples
            # print("tot time to data added: " + repr(time.time()-start_t))
        else:
            samples_that_fit = (
                self.unprocessed_data.shape[0] - self.unprocessed_data_ind
            )
            # need to only add up to end of buffer then process.
            self.unprocessed_data[self.unprocessed_data_ind :, :] = data[
                :samples_that_fit, :
            ]
            self.times[self.unprocessed_data_ind :] = timestamps[:samples_that_fit]
            # use time at center of window
            ts = self.times[int(window_size / 2)]
            # use time at center of window
            # beamformed = acbeamform.AcBeamformed.from_receiver_and_acbeamconfig(
            # receiver=receiver,
            # bf_config=self.bf_config,
            # data_time=ts,
            # verbose=1)
            [pitch, roll, yaw] = receiver.get_pry()
            # TODO: SAM, CHECK
            BF_out = self.BF_obj.calc_beamformed(
                windowed_data=self.unprocessed_data,
                pitch_deg=pitch,
                roll_deg=roll,
                yaw_deg=yaw,
            )

            array_mat = self.BF_obj.array_xyz
            dc = DataContainer_Beamformed_Output_Raw(
                data=BF_out,
                thetas=self.BF_obj.look_angles_bearing,
                phis=self.BF_obj.look_angles_elevation,
                start_time=ts,
                frequencies=self.BF_obj.f_list,
                array_x=array_mat[:, 0],
                array_y=array_mat[:, 1],
                array_z=array_mat[:, 2],
                window_length_s=self.BF_obj.window_length_s,
                sample_rate=self.BF_obj.sample_rate,
                element_mask=self.BF_obj.element_mask,
                mode=self.BF_obj.bf_mode,
                weighting_type=self.BF_obj.weight_mode,
                xform_pitch=pitch,
                xform_roll=roll,
                xform_yaw=yaw,
                element_weights=self.BF_obj.array_weights,
            )
            # put any residual into new buffer
            self.unprocessed_data[0 : num_samples - samples_that_fit, :] = data[
                samples_that_fit:, :
            ]
            self.times[0 : num_samples - samples_that_fit] = timestamps[
                samples_that_fit:
            ]
            self.unprocessed_data_ind = num_samples - samples_that_fit
            # print("tot time to beamform done: " + repr(time.time()-start_t))

            return dc
        return None

    def input_data(self, dc):
        """
        Overload super class to pass receiver through along with data container.
        """
        self.waiting = False
        self.dataframes.put((dc, self.receiver))
