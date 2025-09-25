from .fixture import Fixture
import threading
from kivy.clock import Clock
import numpy as np
import time
from time import sleep


class Fixture_Kivy(Fixture):
    def __init__(self, app):
        self.app = app
        super().__init__()

    def add_kivy_block(
        self, block, input_signal=None, output_signal=None, display_type="debug"
    ):
        self.add_block(block, input_signal, output_signal)
        Clock.schedule_interval(block.kivy_callback, 0.5)
        if display_type == "debug":
            self.app.add_widget(block.widget)
        elif display_type == "map":
            self.app.add_map(block.widget)

    def run_in_thread(self):
        self.process_thread = threading.Thread(target=self.run)
        self.process_thread.start()

    def process(self, t):
        pass

    def run(self):
        while True:
            t = np.datetime64(time.time_ns(), "ns")
            self.process(t)
            for b in self.blocks:
                # while not b.is_waiting():
                #    sleep(0.1)
                b.process(t)
            sleep(0.2)
