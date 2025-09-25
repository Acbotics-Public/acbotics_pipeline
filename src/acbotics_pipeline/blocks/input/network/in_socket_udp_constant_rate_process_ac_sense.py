from abc import ABC
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
from acbotics_pipeline.blocks.input.network.in_socket_udp_process import (
    In_Socket_UDP_Process,
)

import queue
import socket
import threading
from acbotics_pipeline.protocols.udp_data_protocol_ac_sense import (
    UDP_Data_Protocol_Ac_Sense,
)
import struct
from time import sleep
from Cython.Build.Cythonize import multiprocessing
import pyprctl


class In_Socket_UDP_Constant_Rate_Process_Ac_Sense(In_Socket_UDP_Process):
    """
    Receives acoustic data sent over udp.

    Should be paired with on Output_Socket_UDP_Constant_Rate on
    the transmitting system.

    Can support either direct or multicast.
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
        Creates block.

        ip_addr: Address of interface to listen on (local address)
        port: Port to listen on
        multicast: Whether the UDP stream being listened to is a multicast stream.
        """
        self.unprocessed_data = queue.Queue()
        super().__init__(
            ip_addr, port, multicast, multicast_interface, multicast_group, as_process
        )

    def initialize_process(self, out_q):
        """
        Initialize the variables for packet reordering
        """
        self.next_packet_count = None
        self.last_packet_dt = None
        self.misordered_packets = {}
        self.MAX_MISORDERED_PACKETS = 10
        super().initialize_process(out_q)

    def get_protocol(self):
        """
        Return the UDP Data protocol
        """
        return UDP_Data_Protocol_Ac_Sense()

    def run_process(self, out_q):
        """
        Runs the block as a separate process.
        """
        server_queue = multiprocessing.Queue()
        self.initialize_process(server_queue)
        pyprctl.set_name("UDP ACSENSE PROC")

        while True:
            dc = server_queue.get()
            dcs = self.process_dc(dc)
            for dc in dcs:
                out_q.put(dc)

    def run_thread(self):
        """
        Runs the block as a thread.
        """
        self.initialize_process(self.resultframes)
        pyprctl.set_name("UDP ACSENSE THREAD")

        while True:
            dc = self.resultframes.get()
            dcs = self.process_dc(dc)
            for dc in dcs:
                self.send_data(dc)

    def process_dc(self, dc):
        """
        Process data container. Attempt to realign packets if out of order.

        Will skip if at least 10 packets are received after the missed one.
        """
        if self.next_packet_count is None:
            self.next_packet_count = dc.frame_count
        if self.last_packet_dt is None:
            self.last_packet_dt = dc.get_start_time()
        # print("frame count: " + repr(dc.frame_count))
        if self.next_packet_count > dc.frame_count:
            if dc.get_start_time() < self.last_packet_dt:
                print("Discarding old UDP packer")
                # TODO Handle rollover and remote restart
                return []
            else:
                print(
                    "Newer packet with lower count. Resetting count from %d to %d"
                    % (self.next_packet_count, dc.frame_count)
                )
                self.last_packet_dt = dc.get_start_time()
                self.next_packet_count = dc.frame_count
        if self.next_packet_count == dc.frame_count:
            self.next_packet_count = dc.frame_count + 1
            return [dc]

        elif self.next_packet_count < dc.frame_count:
            self.misordered_packets[dc.frame_count] = dc
            dcs = []
            print(
                "Misordered packet. Adding to Queue. Off by: "
                + repr(self.next_packet_count - dc.frame_count)
            )
            while True:
                if len(self.misordered_packets.keys()) == 0:
                    break

                next_misordered_packet_ind = min(self.misordered_packets.keys())
                if next_misordered_packet_ind == self.next_packet_count:
                    print(
                        "Reinserting misordered packet " + repr(self.next_packet_count)
                    )
                    dc = self.misordered_packets.pop(next_misordered_packet_ind)
                    self.next_packet_count = dc.frame_count

                    dcs.append(dc)
                    self.next_packet_count = dc.frame_count + 1

                elif len(self.misordered_packets) > self.MAX_MISORDERED_PACKETS:
                    dc = self.misordered_packets.pop(next_misordered_packet_ind)

                    print(
                        "Excessive misordred packets."
                        + repr(self.misordered_packets)
                        + " Resyncing to "
                        + repr(dc.frame_count)
                    )

                    # self.misordered_packets = {}
                    self.next_packet_count = dc.frame_count
                    dcs.append(dc)
                    self.next_packet_count = dc.frame_count + 1

                else:
                    print(
                        "end of reorder. next_packet_ind = "
                        + repr(next_misordered_packet_ind)
                        + "next packet count = "
                        + repr(self.next_packet_count)
                    )
                    break
            return dcs

    def process(self, process_time):
        """
        Synchronous processing. Called from fixture on a set schedule.

        Empty.
        """
        pass
