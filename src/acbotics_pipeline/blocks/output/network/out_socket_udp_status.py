import icontract
import numpy as np
import socket
from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
import time
from acbotics_pipeline.protocols.udp_status_protocol import UDP_Status_Protocol
from acbotics_pipeline.data_containers.data_container_status import DataContainer_Status

from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP


class Out_Socket_UDP_Status(Out_Socket_UDP):
    def get_protocol(self):
        """
        Returns the status protocol
        """
        return UDP_Status_Protocol()
