from acbotics_pipeline.blocks.base.pr_threaded_process import PR_Threaded_Process
from acbotics_pipeline.data_containers.data_container_nav import DataContainer_Nav
import icontract


class Out_Receiver_Nav_Update(PR_Threaded_Process):
    def __init__(self, receiver):
        """Init the block.

        receiver: refrerence to the receiver to update when new nav comes in"""
        self.receiver = receiver
        super().__init__()

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Nav), "Must be nav container"
    )
    def handle_data(self, dc):
        """Handle a new nav message and update the receiver with the valid portions"""
        nav_time = dc.start_time
        if dc.gps_valid:
            lat = dc.gps_lat
            lon = dc.gps_lon
            # todo. update lat/lon self.receiver.update()
        if dc.orientation_valid:
            pitch = dc.pitch
            roll = dc.roll
            yaw = dc.heading
            self.receiver.set_pry(pitch, roll, yaw, nav_time)
        # todo: velocity and acceleration
