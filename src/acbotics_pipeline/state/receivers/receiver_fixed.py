from scipy.spatial.transform import Rotation as R
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Receiver_Fixed:
    def __init__(self, x, y, z, array_config={}, pitch=0, roll=0, yaw=0, latlon=None):
        self.offset_x = 0
        self.offset_y = 0
        self.offset_z = 0

        if "offset_x" in array_config.keys():
            self.offset_x = array_config["offset_x"]
        if "offset_y" in array_config.keys():
            self.offset_x = array_config["offset_y"]
        if "offset_z" in array_config.keys():
            self.offset_x = array_config["offset_z"]

        self.x = x
        self.y = y
        self.z = z
        self.el_x = np.array(array_config["array_x"])
        self.el_y = np.array(array_config["array_y"])
        self.el_z = np.array(array_config["array_z"])
        if "custom_weights" in array_config.keys():
            # check length:
            if len(array_config["custom_weights"]) != self.get_array_N():
                # remove custom weights and print:
                logger.info(
                    "Custom weights not being used because length does not match element length!!"
                )
                del array_config["custom_weights"]

        self.array_config = array_config

        self.latlon = latlon

        self.set_pry(pitch, roll, yaw)  # pitch around y, roll around x, yaw around z

        self.sample_rate = array_config["sample_rate"]
        self.N = self.get_array_N()
        self.detections_1d_times = []
        self.detections_1d = []
        if "element_mask" in self.array_config.keys():
            if len(array_config["element_mask"]) == self.get_array_N():
                self.element_mask = array_config["element_mask"]
            else:
                logger.info(
                    "Element mask must have the same number of elements as your array! Invalid config, ignoring and using all elements"
                )
                self.element_mask = np.ones(self.get_array_N())
        else:
            self.element_mask = np.ones(self.get_array_N())

    def active(self, process_time):
        return True

    def get_xpos(self, time):
        return self.x

    def get_ypos(self, time):
        return self.y

    def get_zpos(self, time):
        return self.z

    def get_xyz(self, time=None):
        return [self.x, self.y, self.z]

    def set_pry(
        self, pitch, roll, yaw, time=None
    ):  # set pitch roll yaw about array center + offsets
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll

    def set_xyz(self, x, y, z, time=None):  # set x,y,z position of array center
        self.x = x
        self.y = y
        self.z = z

    def get_pry(self, time=None):
        return [self.pitch, self.roll, self.yaw]

    def get_array_locs(
        self, xform=0
    ):  # if xform is unspecified or 0, return array el_x/el_y/el_z; if xform=1, apply rotation
        if xform == 0:
            array_mat_config = np.transpose(np.array([self.el_x, self.el_y, self.el_z]))
            rot = R.from_euler("zyx", [0, 0, 0], degrees="True")
        if xform == 1:
            array_mat_config = np.transpose(
                np.array(
                    [
                        self.el_x + self.offset_x,
                        self.el_y + self.offset_y,
                        self.el_z + self.offset_z,
                    ]
                )
            )
            rot = R.from_euler("zyx", [self.yaw, self.pitch, self.roll], degrees="True")

        out = rot.apply(array_mat_config)

        return out

    def get_array_N(self):
        return len(self.array_config["array_x"])

    def add_detections_1d(self, dc):
        self.detections_1d.append(dc.get_angles())
        self.detections_1d_times.append(dc.get_start_time())

    def get_detections_1d(self):
        return (self.detections_1d_times, self.detections_1d)

    def keys(self):
        return self.keys()


##class Receiver_Mobile:
##    def __init__(self, x, y, z,array_config=None,pitch=0,roll=0,yaw=0,latlon=None):
##        self.x = x
##        self.y = y
##        self.z = z
##        self.array_config=array_config
##        self.latlon=latlon
##        set_pry(pitch,roll,yaw) # pitch around y, roll around x, yaw around z
##        set_array_locs(self.array_config,pitch,roll,yaw)
##
##    def active(self, process_time):
##        return True
##
##    def get_xpos(self, time):
##        return self.x
##
##    def get_ypos(self, time):
##        return self.y
##
##    def get_zpos(self,time):
##        return self.z
##
##    def set_pry(self,pitch,roll,yaw,time):
##        self.pitch=pitch
##        self.yaw=yaw
##        self.roll=roll
##
##    def set_xyz(self,x,y,z,time):
##        self.x=x
##        self.y=y
##        self.roll=roll
##
##    def get_array_locs(self):
##        array_mat_config = np.transpose(np.array([array['array_x'],array['array_y'],array['array_z']]))
##        rot = R.from_euler('zyx',[self.yaw,self.pitch,self.roll],degrees='True')
##        out=rot(array_mat_config)
##
##        return out
##
##
##
