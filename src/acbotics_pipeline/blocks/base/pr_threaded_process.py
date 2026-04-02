import icontract
import numpy as np
from abc import ABC, abstractmethod
import queue
import threading
import time
import pyprctl


class PR_Threaded_Process(ABC):
    def __init__(self, max_qsize=1000, timer_sec=None):
        self.callbacks = []
        self.dataframes = queue.Queue()
        self.thread = threading.Thread(target=self.run_thread)
        self.stop = False
        self.waiting = True
        self.max_qsize = max_qsize
        self.timer_sec = timer_sec
        self.last_time = (
            time.time()
        )  # should we make this a different time to handle accelerated sim?

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
            q_timeout = 2
            if self.timer_sec is not None:
                dt = time.time() - self.last_time
                if dt < q_timeout:
                    q_timeout = dt
            try:
                data_to_process = self.dataframes.get(timeout=q_timeout)
                self.handle_data(data_to_process)
            except queue.Empty:
                pass
            if (
                self.timer_sec is not None
                and time.time() - self.last_time >= self.timer_sec
            ):
                self.timer_callback()
                self.last_time = time.time()
            self.waiting = self.dataframes.empty()

    def timer_callback(self):
        pass  # overload if block needs to use a timer callback

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
