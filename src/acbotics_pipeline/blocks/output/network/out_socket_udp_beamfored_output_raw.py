import icontract
import numpy as np
import socket
from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP
import time
from acbotics_pipeline.protocols.udp_beamform_raw_protocol import (
    UDP_Beamform_Raw_Protocol,
)
from acbotics_pipeline.data_containers.data_container_beamformed_output_raw import (
    DataContainer_Beamformed_Output_Raw,
)


class Out_Socket_UDP_Beamformed_Output_Raw(Out_Socket_UDP):
    def get_protocol(self):
        """
        Returns the raw beamform protocol
        """
        return UDP_Beamform_Raw_Protocol()

    @icontract.require(
        lambda dc: isinstance(dc, DataContainer_Beamformed_Output_Raw),
        "Must be 2D beamform container",
    )
    def handle_data(self, dc):
        """
        Process a beamform data container from preceding block
        """
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
            packet_num=self.packet_num,
        )
        self.packet_num += 1

        ind = 0
        for pkt in data_to_send:
            ind += 1
            while True:
                sent = self.socket.sendto(pkt, (self.ip_addr, self.port))
                if sent > 0:
                    # time.sleep(0.01)
                    break
                print("UDP send failed. resending.")
                time.sleep(0.05)
