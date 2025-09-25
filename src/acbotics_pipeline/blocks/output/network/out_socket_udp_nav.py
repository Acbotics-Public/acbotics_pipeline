import icontract
from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP
from acbotics_pipeline.protocols.udp_nav_protocol import UDP_Nav_Protocol


class Out_Socket_UDP_Nav(Out_Socket_UDP):
    def get_protocol(self):
        return UDP_Nav_Protocol()
