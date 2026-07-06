import icontract
from abc import ABC, abstractmethod

import sys, os
from pathlib import Path
import numpy as np

# # path = Path("os.path.realpath(__file__)").'../'

# path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../")
# # p = str(path.parent.absolute().parent.absolute())
# # print("Adding path: " + p, " base=" + repr(path.absolute()))
# sys.path.append(path)

# path = Path("os.path.realpath(__file__)")
# p = os.path.join(str(path.parent.absolute().parent.absolute().parent.parent),'AcProcess')
# sys.path.append(p)

# Add libs path. Used for kivy backend thqat we need to modify
# path = Path("os.path.realpath(__file__)")
# p = str(path.parent.absolute().parent.absolute())
# new_path = [os.path.join(p, 'libs/garden/garden.matplotlib')]
# new_path.extend(sys.path)
# sys.path = new_path
# print(sys.path)


# sys.path.append(os.path.join(path, "../../AcBeamform/"))
# sys.path.append(os.path.join(path, "../../AcSimulate/"))
# sys.path.append(os.path.join(path, "../../AcDetect/"))

# sys.path.append(os.path.join(path, "../../utils/"))

import time

# import matplotlib.pyplot as plt


class Fixture(ABC):
    def __init__(self):
        self.cpp_blocks = {}
        self.blocks = []
        self.signal_router = {}
        self.next_fig_num = 1

        self.build()

    def add_cpp_block(self, name, block, source=None):
        self.cpp_blocks[name] = block
        if not source is None and source in self.cpp_blocks.keys():
            source_block = self.cpp_blocks[source]
            source_block.register_client(block)

    @abstractmethod
    def build(self):
        pass

    def add_signal_callback(self, signal_name, function):
        if signal_name not in self.signal_router.keys():
            self.signal_router[signal_name] = []
            print("Warning: Adding input signal that is not yet in router")
        self.signal_router[signal_name].append(function)

    def add_block(
        self,
        block,
        input_signal=None,
        output_signal=None,
        named_output_signals=None,
        input_signals=None,
    ):
        self.blocks.append(block)
        if output_signal:
            block.add_callback(self.get_route_signal_callback(output_signal))
            if output_signal not in self.signal_router.keys():
                self.signal_router[output_signal] = []
            else:
                print("Warning: Adding signal already in signal router")
        if named_output_signals is not None:
            for sig in named_output_signals:
                channel_name = sig[0]
                signal_name = sig[1]
                block.add_named_callback(
                    channel_name, self.get_route_signal_callback(signal_name)
                )
                if signal_name not in self.signal_router.keys():
                    self.signal_router[signal_name] = []
                else:
                    print("Warning: Adding signal already in signal router")

        if input_signal:
            if input_signal not in self.signal_router.keys():
                self.signal_router[input_signal] = []
                print("Warning: Adding input signal that is not yet in router")
            self.signal_router[input_signal].append(block.input_data)

        if input_signals:
            for sig in input_signals:
                if sig not in self.signal_router.keys():
                    self.signal_router[sig] = []
                    print("Warning: Adding input signal that is not yet in router")
                self.signal_router[sig].append(block.input_data)

    def route_signal(self, dc, sig_name):
        if sig_name not in self.signal_router.keys():
            print("Warning. Attempting to send signal to no where")
            return
        for cb in self.signal_router[sig_name]:
            cb(dc)

    def get_route_signal_callback(self, sig_name):
        return lambda dc: self.route_signal(dc, sig_name)

    def get_next_fig_num(self):
        v = self.next_fig_num
        self.next_fig_num += 1
        return v

    def run(self, sleep_time=0.0):
        for name, block in self.cpp_blocks.items():
            print("Running Cpp block" + name)
            block.run()
        while True:
            t = np.datetime64(time.time_ns(), "ns")
            for b in self.blocks:
                while not b.is_waiting():
                    time.sleep(0.1)
                b.process(t)
            time.sleep(sleep_time)


#            plt.pause(0.01)
# self.blocks[0].thread.join()
# time.sleep(1000)
