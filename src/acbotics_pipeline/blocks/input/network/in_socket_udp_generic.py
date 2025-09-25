"""
Created on Apr 25, 2024

@author: oscar
"""

from acbotics_pipeline.blocks.input.network.in_socket_udp_process import (
    In_Socket_UDP_Process,
)
from acbotics_pipeline.protocols.udp_generic_protocol import UDP_Generic_Protocol


class In_Socket_UDP_Generic(In_Socket_UDP_Process):
    def get_protocol(self):
        """
        Returns the Pressure/Temperature protocol.
        """
        return UDP_Generic_Protocol()
