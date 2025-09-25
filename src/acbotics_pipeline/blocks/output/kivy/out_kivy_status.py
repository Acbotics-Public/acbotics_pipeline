import icontract
import numpy as np

from kivy.clock import mainthread
from queue import Queue, Empty
from gui.kivy.widgets.status_panel import Status_Panel


class Out_Kivy_Status:
    def __init__(self):
        self.unprocessed_status = Queue()
        self.widget = Status_Panel()

    @mainthread
    def kivy_callback(self, dt):
        # process_time = self.process_time
        try:
            dc = self.unprocessed_status.get(block=False)
            self.widget.update_data(dc)
        except Empty:
            # if nothing to get, ignore
            pass

    def input_data(self, dc):
        self.unprocessed_status.put(dc)

    def is_waiting(self):
        return True

    def process(self, process_time):
        pass
