import icontract
import socket
from abc import ABC, abstractmethod
from acbotics_pipeline.blocks.base.pr_multiprocess_process import (
    Pr_Multiprocess_Process,
)
import netifaces as ni


class Out_Socket_UDP(Pr_Multiprocess_Process, ABC):
    """
    Abstract base class for blocks sending udp output.

    Can be run as either thread or process.
    """

    def __init__(
        self,
        ip_addr,
        port,
        multicast=False,
        multicast_ttl=1,
        multicast_interface=None,
        as_process=False,
    ):
        """
        Create the block
        ip_addr: target ip address to send to.
        port: port to send udp to.
        multicast: True is sending multicast packets.
        multicast_ttl: How far packets should propogate.
        multicast_interface: The interface the multicast packets should be sent over (ie eth0)
        """
        # self.unprocessed_data = Queue()
        self.ip_addr = ip_addr
        self.port = port
        self.multicast = multicast
        self.multicast_ttl = multicast_ttl
        self.multicast_interface = multicast_interface
        super().__init__(as_process=as_process)
        # self.packet_num = None

    def initialize_process(self):
        self.socket = socket.socket(
            socket.AF_INET,  # Internet
            socket.SOCK_DGRAM,  # | socket.SOCK_NONBLOCK,
            socket.IPPROTO_UDP,
        )  # UDP
        if self.multicast:
            self.socket.setsockopt(socket.IPPROTO_IP, self.multicast_ttl, 32)
            if not self.multicast_interface is None:
                ip = ni.ifaddresses(self.multicast_interface)[ni.AF_INET][0]["addr"]
                self.socket.setsockopt(
                    socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip)
                )

        self.values_per_frame = 32000
        self.packet_num = 0
        self.frame_count = 0
        self.protocol = self.get_protocol()

    @abstractmethod
    def get_protocol(self):
        """Override with method return protocol for block"""
        pass

    def handle_data(self, dc):
        """
        Method called when data is available from preceeding block
        """
        data_to_send = self.protocol.encode(dc)
        self.socket.sendto(data_to_send, (self.ip_addr, self.port))

    def __del__(self):
        """
        Close socket on object destruction
        """
        if self.socket:
            self.socket.close()
