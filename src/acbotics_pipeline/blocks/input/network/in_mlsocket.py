from abc import ABC
import icontract
import numpy as np
from acbotics_pipeline.data_containers.data_container_constant_rate import (
    DataContainer_Constant_Rate,
)
import queue
import mlsocket
import threading


class In_MLSocket(ABC):
    @icontract.require(
        lambda start_time: isinstance(start_time, np.datetime64),
        "start_time must be datetime64",
    )
    def __init__(self, ip_addr, port, sample_rate, start_time):
        self.sample_rate = sample_rate
        self.ip_addr = ip_addr
        self.port = port
        self.callbacks = []
        self.start_time = start_time
        self.unprocessed_data = queue.Queue()
        self.socket = mlsocket.MLSocket()
        self.socket.bind((self.ip_addr, self.port))
        self.thread = threading.Thread(target=self.server_thread)
        self.thread.start()

    def __del__(self):
        if self.socket:
            self.socket.close()

    def get_number_of_input_channels(self):
        return 0

    def get_number_of_output_channels(self):
        return 1

    def add_callback(self, function):
        self.callbacks.append(function)

    def server_thread(self):
        self.socket.listen()
        self.conn, self.conn_address = self.socket.accept()
        while True:
            data = self.conn.recv(
                1024
            )  # This will block until it receives all the data send by the client, with the step size of 1024 bytes.
            print("Received data")
            print(data.shape)
            self.unprocessed_data.put(data)

    def process(self, process_time):
        print("process mlsocket")
        while not self.unprocessed_data.empty():
            d = self.unprocessed_data.get()
            dc = DataContainer_Constant_Rate(d, self.sample_rate, self.start_time)
            print("socket_callback")
            for c in self.callbacks:
                c(dc)
