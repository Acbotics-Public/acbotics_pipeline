import icontract


from blocks.base.pr_multiprocess_process import Pr_Multiprocess_Process
from data_containers.data_container_angle_list import DataContainer_Angle_List
from data_containers.data_container_beamformed_output_1d import (
    DataContainer_Beamformed_Output_1D,
)
import AcDetect


class Pr_Detect_BF_Peak_1D(Pr_Multiprocess_Process):
    def __init__(self, max_peaks, as_process=False):
        self.max_peaks = max_peaks
        super().__init__(as_process=as_process)

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_1D),
        "Argument must be 2d beamformed data",
    )
    def handle_data(self, dc):
        detects_1d = AcDetect.detect_BF_peaks1d(
            dc.get_angles(), dc.data, self.max_peaks
        )
        dc_out = DataContainer_Angle_List(data=detects_1d, start_time=dc.start_time)
        return dc_out
