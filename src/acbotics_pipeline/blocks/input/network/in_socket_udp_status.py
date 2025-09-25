from acbotics_pipeline.blocks.input.network.in_socket_udp_process import (
    In_Socket_UDP_Process,
)
from acbotics_pipeline.protocols.udp_status_protocol import UDP_Status_Protocol


class In_Socket_UDP_Status(In_Socket_UDP_Process):
    def get_protocol(self):
        """
        Returns the navigation protocol.
        """
        return UDP_Status_Protocol()
