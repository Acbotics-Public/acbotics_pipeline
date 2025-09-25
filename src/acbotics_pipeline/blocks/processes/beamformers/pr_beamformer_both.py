import icontract
import numpy as np
import math
import pyprctl
import queue
import multiprocessing
from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_raw import (
    DataContainer_Beamformed_Output_Raw,
)

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
        self.unprocessed_data = np.array([])
        self.times = []
        super().initialize_process()

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
        window_size = self.bf_config["BF_window_length_s"] * receiver.sample_rate

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
        if self.unprocessed_data.shape[0] > window_size:
            x = self.unprocessed_data[0:window_size, 0:]
            # use time at center of window
            ts = self.times[int(window_size / 2)]
            new_start = math.floor(window_size)
            self.unprocessed_data = self.unprocessed_data[window_size:]
            self.times = self.times[new_start:]
            # beamformed = acbeamform.AcBeamformed.from_receiver_and_acbeamconfig(
            # receiver=receiver,
            # bf_config=self.bf_config,
            # data_time=ts,
            # verbose=1)
            [pitch, roll, yaw] = receiver.get_pry()
            # TODO: SAM, CHECK
            BF_out = self.BF_obj.calc_beamformed(
                windowed_data=x, pitch_deg=pitch, roll_deg=roll, yaw_deg=yaw
            )
            BF_old = acbeamform_old.AcBeamformed.from_receiver_and_acbeamconfig(
                receiver=receiver, bf_config=self.bf_config, data_time=ts, verbose=1
            )
            BF_old.process_data_beamform(windowed_data=x, data_time=ts)
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
            return dc
        return None

    def input_data(self, dc):
        """
        Overload super class to pass receiver through along with data container.
        """
        self.waiting = False
        self.dataframes.put((dc, self.receiver))
