from abc import ABC, abstractmethod
import queue
import socket
import threading
import multiprocessing
import struct
import pyprctl
import netifaces as ni

from time import sleep


class In_Socket_UDP_Process(ABC):
    """
    Base class for UDP inputs.

    Subclasses override protocol with their needed protocol.

    Can be run as either a thread or process depending on init.
    """

    def __init__(
        self,
        ip_addr,
        port,
        multicast=False,
        multicast_interface=None,
        multicast_group=None,
        as_process=True,
    ):
        """
        Create block.

        ip_addr: Address of interface to listen on (local address)
        port: Port to listen on
        multicast: Whether the UDP stream being listened to is a multicast stream.
        as_process: Whether to run as a process (True) or thread (False)
        """
        self.multicast_interface = multicast_interface
        self.multicast_group = multicast_group
        self.callbacks = []
        self.as_process = as_process
        if as_process:
            self.resultframes = multiprocessing.Queue()
            self.multi_process = multiprocessing.Process(
                target=self.run_process, args=(self.resultframes,)
            )
            self.thread = threading.Thread(target=self.run_output_thread)
        else:
            self.resultframes = queue.Queue()
            self.thread = threading.Thread(target=self.run_thread)

        self.stop = False
        self.waiting = True
        self.multicast = multicast
        self.ip_addr = ip_addr
        self.port = port
        self.callbacks = []
        self.protocol = self.get_protocol()

        self.start()  # TODO. This may want to be moved out from here to separate start from block creation.

    def initialize_process(self, out_q):
        """
        Called from inside the process or thread on startup. Override in sub classes
        with any needed behavior.
        """
        pyprctl.set_name(repr(type(self))[-15:])

        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM  # Internet
        )  # UDP
        if self.multicast:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # We may want to lower this TTL value? Shouldn't need to extend past local
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

            # This is set to 1 by default; don't need to set explicitly
            # self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

            self.socket.bind(("", self.port))

            if not self.multicast_group is None:
                ip = self.multicast_group
            elif not self.multicast_interface is None:
                ip = ni.ifaddresses(self.multicast_interface)[ni.AF_INET][0]["addr"]

            mreq = struct.pack(
                "4s4s",
                socket.inet_aton(ip),
                socket.inet_aton(self.ip_addr),
            )
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        else:
            self.socket.bind((self.ip_addr, self.port))

        self.thread = threading.Thread(target=self.server_thread, args=(out_q,))
        self.thread.start()

    def start(self):
        """
        Starts the threads and processes depending on configuration
        """
        self.stop = False
        self.thread.start()
        if self.as_process:
            self.multi_process.start()

    def run_process(self, out_q):
        """
        Runs the block as a separate process.
        """
        self.initialize_process(out_q)

        while True:
            sleep(1)

    def run_thread(self):
        """
        Runs the block as a thread.
        """
        self.initialize_process(self.resultframes)

        while True:
            dc = self.resultframes.get()
            self.send_data(dc)

    def __del__(self):
        """
        closes socket on object deletion
        """
        if self.socket:
            self.socket.close()

    @abstractmethod
    def get_protocol(self):
        """
        Override in subclass with method returning protocol object
        """
        pass

    def is_waiting(self):
        """
        Placeholder for waiting functionality. TODO.
        """
        return True

    def add_callback(self, function):
        """
        Registers function as a callback to be called when data is available.
        """
        self.callbacks.append(function)

    def server_thread(self, out_q):
        """
        This thread handles receiving UDP data and decoding it.
        """
        while True:
            data, addr = self.socket.recvfrom(65535)
            # check header
            dc = self.protocol.decode(data)
            if dc is not None:
                out_q.put(dc)

    def run_output_thread(self):
        """
        This thread watches for data back from the process. When data comes back, it will call send
        data to make the callbacks
        """
        while True:
            dc = self.resultframes.get()
            if not dc is None:
                self.send_data(dc)

    def send_data(self, dc):
        """
        Send data container to subscribed callbacks.
        """
        for c in self.callbacks:
            c(dc)

    def process(self, process_time):
        """
        Synchronous processing. Called from fixture on a set schedule.

        Leave empty for most implementations.
        """
        pass
