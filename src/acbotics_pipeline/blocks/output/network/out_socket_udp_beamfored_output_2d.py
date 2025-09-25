import icontract
import numpy as np
import socket
from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP
import time
from acbotics_pipeline.protocols.udp_beamform_2d_protocol import (
    UDP_Beamform_2D_Protocol,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_2d import (
    DataContainer_Beamformed_Output_2D,
)


class Out_Socket_UDP_Beamformed_Output_2D(Out_Socket_UDP):
    def get_protocol(self):
        return UDP_Beamform_2D_Protocol()

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_2D),
        "Must be 2D beamform container",
    )
    def handle_data(self, dc):
        # print("handle beamform udp output")
        data_to_send = self.protocol.encode(
            data_array=dc.data,
            bearings=np.array(dc.get_thetas()),
            elevations=np.array(dc.get_phis()),
            start_time=dc.get_start_time(),
            frequencies=dc.frequencies,
            array_x=dc.array_x,
            array_y=dc.array_y,
            array_z=dc.array_z,
            element_mask=dc.element_mask,
            element_weights=dc.element_weights,
            sample_rate=dc.sample_rate,
            window_length_s=dc.window_length_s,
            pitch=dc.xform_pitch,
            roll=dc.xform_roll,
            yaw=dc.xform_yaw,
            mode=dc.mode,
            weighting_type=dc.weighting_type,
            packet_num=0,
        )

        # print("send beamform udp to " + repr(self.ip_addr) + ":" + repr(self.port))
        self.socket.sendto(data_to_send, (self.ip_addr, self.port))
