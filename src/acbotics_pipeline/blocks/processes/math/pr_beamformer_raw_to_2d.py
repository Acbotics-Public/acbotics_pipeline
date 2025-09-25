import icontract
import numpy as np

from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_raw import (
    DataContainer_Beamformed_Output_Raw,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)


class Pr_Beamformer_Raw_To_2D(Pr_Multiprocess_Process):
    """
    Converts a raw beamform into a 2D beamform by taking mean over frequencies.
    """

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_Raw),
        "Argument must be 2d beamformed data",
    )
    def handle_data(self, dc):
        """
        Process a raw beamform into a 2D beamform.
        """
        data = np.sum(dc.data, 2) / (dc.data.shape[2])
        dc_out = DataContainer_Beamformed_Output_2D(
            data,
            thetas=dc.thetas,
            phis=dc.phis,
            frequencies=dc.frequencies,
            start_time=dc.start_time,
            array_x=dc.array_x,
            array_y=dc.array_y,
            array_z=dc.array_z,
            window_length_s=dc.window_length_s,
            sample_rate=dc.sample_rate,
            element_mask=dc.element_mask,
            mode="mean",
            weighting_type=dc.weighting_type,
            xform_pitch=dc.xform_pitch,
            xform_roll=dc.xform_roll,
            xform_yaw=dc.xform_yaw,
            element_weights=dc.element_weights,
        )
        return dc_out
