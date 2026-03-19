import icontract
import numpy as np
import time
from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP
from acbotics_pipeline.protocols.udp_generic_protocol import UDP_Generic_Protocol
import copy

from acbotics_pipeline.protocols.sensor_payloads import default_sensor_mapping


class Out_Socket_UDP_Sensor(Out_Socket_UDP):

    def __init__(self, sensor_dict=default_sensor_mapping, *args, **kwargs):
        self.sensor_dict = copy.copy(sensor_dict)
        super().__init__(*args, **kwargs)

    def get_protocol(self, sensor=None):
        """
        Returns the generic sensor protocol
        """
        if sensor is None:
            return UDP_Generic_Protocol()
        return self.sensor_dict[sensor]

    def handle_data(self, dc):
        """
        Method called when data is available from preceeding block
        """
        data_to_send = self.get_protocol(dc.sensor_type).encode(dc)
        if data_to_send is not None:
            self.socket.sendto(data_to_send, (self.ip_addr, self.port))
