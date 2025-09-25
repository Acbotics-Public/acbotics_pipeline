import icontract
from abc import ABC, abstractmethod
import multiprocessing
import threading
import queue

# TODO Make work and test
import pyprctl


class Pr_Multiprocess_Process(ABC):
    """
    This forms the base class for blocks that have an input and output. It
    can be used to either run the blocks as a separate thread or process.

    Running as a process incurs additional overhead with parameter passing,
    but allows it to run on a separate cpu. It is also useful for decoupling
    time sensitive (ie UDP receive) operations from the gui when the gui is
    ruinning in the main thread."""

    def __init__(self, as_process=False):
        """Create the block.

        as_process: if true, this block will run as a separate process.
                    Otherwise it will run as a thread.
        """
        self.callbacks = (
            []
        )  # list of functions to call with the data container once data is available.
        self.as_process = as_process

        if as_process:
            # For multiprocessing, we need a queue for input and output.
            # Multiprocessing queues are used in this case.
            self.dataframes = multiprocessing.Queue()
            self.resultframes = multiprocessing.Queue()
            self.multi_process = multiprocessing.Process(
                target=self.run_process, args=(self.dataframes, self.resultframes)
            )
            # the thread runs in the main process and is used to take data out
            # of the processes output queue and send them to the following blocks.
            self.thread = threading.Thread(target=self.run_output_thread)
        else:
            # For running as a thread, the overhead of a multiprocessing
            # queue is not needed. A separate output thread is also  not needed/
            self.dataframes = queue.Queue()
            self.thread = threading.Thread(target=self.run_thread)

        self.stop = False
        self.waiting = True
        # begin the threads or process.
        self.start()  # TODO. This may want to be moved out from here to separate start from block creation.

    def initialize_process(self):
        """
        Called from inside the process or thread on startup. Override in sub classes
        with any needed behavior.
        """
        pass

    def start(self):
        """
        Starts the threads and processes depending on configuration
        """
        self.stop = False
        self.thread.start()
        if self.as_process:
            self.multi_process.start()

    def input_data(self, dc):
        """
        Processes an incoming data container. Used as callback to preceeding block in pipeline.
        """
        self.waiting = False
        self.dataframes.put(dc)

    def add_callback(self, function):
        """
        Registers function as a callback to be called when data is available.
        """
        self.callbacks.append(function)

    def run_process(self, in_q, out_q):
        """
        Runs the block as a separate process.
        """
        self.initialize_process()
        pyprctl.set_name(repr(type(self))[-15:])  # used to control process name in htop
        while True:
            data_to_process = in_q.get()
            # print(repr(type(self)) + ": queue size " + repr(in_q.qsize()))
            dc = self.handle_data(data_to_process)
            if not dc is None:
                out_q.put(dc)

    def run_thread(self):
        """
        Runs the block as a thread
        """
        self.initialize_process()
        pyprctl.set_name(repr(type(self))[-15:])  # used to control thread name in htop

        while True:
            data_to_process = self.dataframes.get()
            dc = self.handle_data(data_to_process)
            if not dc is None:
                self.send_data(dc)

    def is_waiting(self):
        """
        Placeholder for waiting functionality. TODO.
        """
        # Maybe implement?
        return True

    def stop_thread(self):
        """
        Stop the running thread
        """
        self.stop = True

    def run_output_thread(self):
        """
        This thread watches for data back from the process. When data comes back, it will call send
        data to make the callbacks
        """
        while True:
            dc = self.resultframes.get()
            if not dc is None:
                self.send_data(dc)

    @abstractmethod
    def handle_data(self, data_to_process):
        """
        Called with data container when data is available to process.
        Override in subclass to provide block behavior
        """
        pass

    def send_data(self, data_to_send):
        """
        Send data container to subscribed callbacks.
        """
        for c in self.callbacks:
            c(data_to_send)

    def process(self, process_time):
        """
        Synchronous processing. Called from fixture on a set schedule.

        Leave empty for most implementations.
        """
        pass
