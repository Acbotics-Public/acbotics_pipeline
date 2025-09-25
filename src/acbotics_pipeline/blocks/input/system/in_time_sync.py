import icontract
import time
import os

import threading

# Keep trying to sync time to ntp. Once time syncs,
# Call the callbacks to trigger processes that should only start once
# time is valid


class In_Time_Sync:
    def __init__(self, target_ip):
        self.thread = threading.Thread(target=self.run_thread)
        self.callbacks = []
        self.target_ip = target_ip
        self.done = False
        self.thread.start()

    def is_waiting(self):
        return True

    def add_callback(self, function):
        self.callbacks.append(function)

    def process(self, process_time):
        pass

    def run_thread(self):
        while True:
            retv = os.system("ntpdate %s" % (self.target_ip))
            if retv == 0:
                break
            print("Waiting for valid time sync")
            time.sleep(1)
        for c in self.callbacks:
            c(None)
        self.done = True
