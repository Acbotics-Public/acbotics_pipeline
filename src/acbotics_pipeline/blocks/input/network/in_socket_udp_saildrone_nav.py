from acbotics_pipeline.blocks.input.network.in_socket_udp_process import (
    In_Socket_UDP_Process,
)
from acbotics_pipeline.protocols.udp_saildrone_nav_protocol import (
    UDP_Saildrone_Nav_Protocol,
)


class In_Socket_UDP_Saildrone_Nav(In_Socket_UDP_Process):
    def get_protocol(self):
        """
        Returns the saildrone custom navigation protocol.
        """
        return UDP_Saildrone_Nav_Protocol()
