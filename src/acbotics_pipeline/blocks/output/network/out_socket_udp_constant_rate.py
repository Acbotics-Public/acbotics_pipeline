import icontract
import numpy as np
import time
from acbotics_pipeline.blocks.output.network.out_socket_udp import Out_Socket_UDP
from acbotics_pipeline.protocols.udp_data_protocol import UDP_Data_Protocol


class Out_Socket_UDP_Constant_Rate(Out_Socket_UDP):

    def __init__(self, force_endian=None, *args, **kwargs):
        self.force_endian = force_endian
        super().__init__(*args, **kwargs)

    def get_protocol(self):
        """
        Returns the constant rate data protocol
        """
        return UDP_Data_Protocol()

    @icontract.require(lambda dc: dc.is_constant_rate(), "sample_rate must be constant")
    def handle_data(self, dc):
        """
        Process a data container from preceding block
        """
        start_ind = 0
        num_channels = dc.data.shape[0]
        ts = dc.get_start_time()
        while start_ind < dc.data.shape[1]:
            step = int(self.values_per_frame / num_channels)
            next_ind = start_ind + step
            d = dc.data[:, start_ind:next_ind]
            data_to_send = self.protocol.encode(
                d,
                dc.get_sample_rate(),
                ts,
                1.0,
                # self.packet_num,
                force_endian=self.force_endian,
                adc_count=dc.start_count,
                tick_time=dc.tick_time,
                packet_number=dc.frame_count,
            )  # dc.scale)
            ts = ts + np.timedelta64(
                int((d.shape[1] * 1e9) / dc.get_sample_rate()), "ns"
            )
            self.packet_num += 1
            while True:
                sent = self.socket.sendto(data_to_send, (self.ip_addr, self.port))
                if sent > 0:
                    break
                time.sleep(0.1)
            start_ind = next_ind
        return None
