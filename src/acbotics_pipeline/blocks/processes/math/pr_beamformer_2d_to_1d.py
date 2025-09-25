import icontract
import numpy as np

from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)


class Pr_Beamformer_2D_To_1D(Pr_Multiprocess_Process):
    """Block to convert 2D beamformed data into 1D data.
    Uses sum over elevations."""

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_2D),
        "Argument must be 2d beamformed data",
    )
    def handle_data(self, dc):
        """Process a beamformed result from 2d to 1d and send along"""
        start_time = dc.start_time
        data = np.sum(dc.data, 1)
        dc_out = DataContainer_Beamformed_Output_1D(data, dc.thetas, start_time)
        return dc_out
