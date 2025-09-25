from acbotics_pipeline.blocks.input.network.in_socket_udp_process import (
    In_Socket_UDP_Process,
)
from acbotics_pipeline.protocols.udp_beamform_raw_protocol import (
    UDP_Beamform_Raw_Protocol,
)
import queue
import threading
from time import sleep


class PartialPacket:
    """Helper class for holding partial beamformed messages.
    Added to with each new packet received. Order of packet
    inputs is not guaranteed"""

    def __init__(self):
        self.num_packets = None
        self.packets = {}

    def add_packet(self, index, data):
        """Add a new packet with sub_index of index"""
        self.packets[index] = data

    def is_complete(self):
        """
        Return true if the packet is complete (number of packets matches expected)
        """
        if self.num_packets is None:
            return False
        if len(self.packets.keys()) == self.num_packets:
            return True
        return False

    def assemble(self):
        """
        Returns data as a single Mega packet. Should only be called on a complete object.
        """
        ordered_keys = sorted(self.packets.keys())
        data = b""
        for k in ordered_keys:
            data = data + self.packets[k]
        return data


class In_Socket_UDP_Beamform_Raw_Process(In_Socket_UDP_Process):
    """Block that receives beamformed raw data over udp protocol.

    Raw beamformed data requires multiple udp packets due to size.
    """

    def __init__(self, ip_addr, port, multicast=False, as_process=True):
        """Creates block.

        ip_addr: Address of interface to listen on (local address)
        port: Port to listen on
        multicast: Whether the UDP stream being listened to is a multicast stream.
        """
        self.partial_packets = {}
        self.last_packet_num = -1
        self.unprocessed_data = queue.Queue()

        super().__init__(
            ip_addr=ip_addr, port=port, multicast=multicast, as_process=as_process
        )

    def get_protocol(self):
        """
        Returns the Raw beamforming protocol
        """
        return UDP_Beamform_Raw_Protocol()

    def server_thread(self, out_q):
        """
        This thread handles receiving UDP data and decoding it.

        Overrides base class to incorporate reassembly of data across multiple
        packets.
        """
        print("Running server thread Beamformed")

        while True:
            data, addr = self.socket.recvfrom(65535)  # buffer size is 1024 bytes
            pp = None
            if self.protocol.is_start_packet(data):
                packet_num = self.protocol.get_packet_num(data)
                num_packets = self.protocol.get_num_packets(data)
                if not packet_num in self.partial_packets.keys():
                    self.partial_packets[packet_num] = PartialPacket()
                pp = self.partial_packets[packet_num]
                pp.num_packets = num_packets
                pp.add_packet(0, data)

            elif self.protocol.is_continued_packet(data):
                packet_num = self.protocol.get_continued_packet_num(data)
                sub_packet_index = self.protocol.get_continued_subpacket_index(data)
                if not packet_num in self.partial_packets.keys():
                    self.partial_packets[packet_num] = PartialPacket()
                pp = self.partial_packets[packet_num]
                pp.add_packet(
                    sub_packet_index, self.protocol.get_continued_payload(data)
                )

            if not pp is None:
                if pp.is_complete():
                    # print(self.partial_packets)
                    dc = self.protocol.decode(pp.assemble())
                    print("roll, pitch yaw ...")
                    print(dc.xform_roll)
                    print(dc.xform_pitch)
                    print(dc.xform_yaw)

                    self.last_packet_num = packet_num
                    self.partial_packets.pop(packet_num)
                    if dc is not None:
                        out_q.put(dc)
                    else:
                        print("Failed to parse beamformed data")
