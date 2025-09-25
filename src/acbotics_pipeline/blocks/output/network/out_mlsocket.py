import icontract
import csv
import numpy as np
import struct
from queue import Queue
import mlsocket
import threading


class Out_MLSocket:
    def __init__(self, ip_addr, port):
        self.unprocessed_data = Queue()
        self.ip_addr = ip_addr
        self.port = port
        self.socket = mlsocket.MLSocket()
        self.socket.connect((self.ip_addr, self.port))
        self.thread = threading.Thread(target=self.run_thread)
        self.thread.start()

    def get_number_of_input_channels(self):
        return 1

    def get_number_of_output_channels(self):
        return 0

    @icontract.require(
        lambda dc: dc.is_constant_rate(), "sample_rate must be constant for wav output"
    )
    def input_data(self, dc):
        self.unprocessed_data.put(dc)

    def __del__(self):
        if self.socket:
            self.socket.close()

    def run_thread(self):
        while True:
            print("Unprocessed_len= " + repr(self.unprocessed_data.qsize()))
            data_to_process = self.unprocessed_data.get()
            if data_to_process.is_constant_rate():
                print("Sending data")
                self.socket.send(
                    data_to_process.data
                )  # After sending the data, it will wait until it receives the reponse from the server
            else:
                raise Exception

    def process(self, process_time):
        pass
