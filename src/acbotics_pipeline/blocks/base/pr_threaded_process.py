import icontract
import numpy as np
from abc import ABC, abstractmethod
import queue
import threading
import time
import pyprctl


class PR_Threaded_Process(ABC):
    def __init__(self, max_qsize=1000):
        self.callbacks = []
        self.dataframes = queue.Queue()
        self.thread = threading.Thread(target=self.run_thread)
        self.stop = False
        self.waiting = True
        self.max_qsize = max_qsize

        self.start()  # TODO. This may want to be moveed out from here to separate start from block creation.

    def start(self):
        self.stop = False
        self.thread.start()

    def input_data(self, dc):
        self.waiting = False  # we have data to process
        self.dataframes.put(dc)
        while self.dataframes.qsize() > self.max_qsize:
            try:
                self.dataframes.get_nowait()
            except queue.Empty:
                pass

    def add_callback(self, function):
        self.callbacks.append(function)

    def run_thread(self):
        pyprctl.set_name(repr(type(self))[-15:])
        while True:
            if self.stop:
                break
            try:
                data_to_process = self.dataframes.get(timeout=2)
            except (
                queue.Empty
            ):  # Timeout and empty added so it can check for stop without receiving data
                continue
            st = time.process_time()

            self.handle_data(data_to_process)
            self.waiting = self.dataframes.empty()

    def is_waiting(self):
        # verify this is actually thread safe
        return (self.dataframes.empty()) and self.waiting

    def stop_thread(self):
        self.stop = True

    def __del__(self):
        self.stop_thread()

    @abstractmethod
    def handle_data(self, data_to_process):
        pass

    def process(self, process_time):
        # Deprecated with threaded architecture? plan to remove
        pass

    def send_data(self, data_to_send):
        for c in self.callbacks:
            c(data_to_send)
