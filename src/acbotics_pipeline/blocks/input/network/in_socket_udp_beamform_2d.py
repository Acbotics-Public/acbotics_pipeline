from acbotics_pipeline.blocks.input.network.in_socket_udp_process import (
    In_Socket_UDP_Process,
)
from acbotics_pipeline.protocols.udp_beamform_2d_protocol import (
    UDP_Beamform_2D_Protocol,
)


class In_Socket_UDP_Beamform_2D(In_Socket_UDP_Process):
    def get_protocol(self):
        return UDP_Beamform_2D_Protocol()
