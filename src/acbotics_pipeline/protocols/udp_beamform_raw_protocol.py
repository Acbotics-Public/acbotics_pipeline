import struct
from collections import namedtuple
import copy
import numpy
import sys
from acbotics_pipeline.data_containers.data_container_beamformed_output_raw import (
    DataContainer_Beamformed_Output_Raw,
)
import numpy as np
import math


class UDP_Beamform_Raw_Protocol:
    def __init__(self):
        self.VERSION_MAJOR_IND = 2
        self.VERSION_MINOR_IND = 3
        self.version_major = 0
        self.version_minor = 2
        # define header info by data size (see struct docs for reference) and field name
        header_info = [
            ("B", "ID1"),
            ("B", "ID2"),
            ("B", "SID1"),
            ("B", "SID2"),
            ("B", "VER_MAJ"),
            ("B", "VER_MIN"),
            ("B", "ENDIAN"),
            ("I", "NUM_ELEMENTS"),
            ("I", "NUM_FREQUENCIES"),
            ("I", "NUM_THETAS"),
            ("I", "NUM_PHIS"),
            ("B", "INDEX_SIZE"),
            ("B", "DATA_SIZE"),
            ("I", "SAMPLE_RATE"),
            ("d", "WINDOW_LENGTH_S"),
            ("q", "START_TIME"),
            ("d", "XFORM_PITCH"),
            ("d", "XFORM_ROLL"),
            ("d", "XFORM_YAW"),
            ("c", "MODE"),
            ("c", "WEIGHTING_TYPE"),
            ("I", "NUM_PACKETS"),
            ("I", "PACKET_NUM"),
        ]
        # mode, fmin, fmax
        # packet splitting
        # packet index
        self.header_fmt = "!" + "".join([l[0] for l in header_info])
        self.Header_Data = namedtuple(
            "header_data", " ".join([l[1] for l in header_info])
        )
        # Add scale field
        self.header_length_b = struct.calcsize(self.header_fmt)

        header_contd_info = [
            ("B", "ID1"),
            ("B", "ID2"),
            ("B", "SID1"),
            ("B", "SID2"),
            ("I", "SUB_PACKET_INDEX"),
            ("I", "PACKET_NUM"),
        ]
        self.header_contd_fmt = "!" + "".join([l[0] for l in header_contd_info])
        self.Header_Contd_Data = namedtuple(
            "header_contd_data", " ".join([l[1] for l in header_contd_info])
        )
        self.header_contd_length_b = struct.calcsize(self.header_contd_fmt)

        self.weight_type_lookup = {
            "B": "bartlett",
            "H": "hanning",
            "N": "no",
            "C": "custom",
        }
        self.weight_type_reverse_lookup = {
            v: k for k, v in self.weight_type_lookup.items()
        }

    def decode_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        if not data[0] == ord("A") or not data[1] == ord("C"):
            print("ignoring unrecognized packet header: " + repr(data[0:2]))
            return None
        if not data[2] == ord("B") or not data[3] == ord("R"):
            print("ignoring wrong type of base message: " + repr(data[2:4]))
            return None

        # extract protocol version
        version_major = data[self.VERSION_MAJOR_IND]
        version_minor = data[self.VERSION_MINOR_IND]
        # eventually use version number to get proper format
        header = self.Header_Data._make(
            struct.unpack(self.header_fmt, data[0 : self.header_length_b])
        )
        return header

    def decode_continued_header(self, data):
        if len(data) < 4:
            print("packet too short. " + repr(data))
            return None
        if not data[0] == ord("A") or not data[1] == ord("C"):
            print("ignoring unrecognized packet header: " + repr(data[0:2]))
            return None
        if not data[2] == ord("B") or not data[3] == ord("C"):
            print("ignoring wrong type of continued message: " + repr(data[2:4]))
            return None

        # extract protocol version
        version_major = data[self.VERSION_MAJOR_IND]
        version_minor = data[self.VERSION_MINOR_IND]
        # eventually use version number to get proper format
        header = self.Header_Contd_Data._make(
            struct.unpack(self.header_contd_fmt, data[0 : self.header_contd_length_b])
        )
        return header

    def calculate_array_x_start_index(self, header):
        return self.header_length_b

    def calculate_array_y_start_index(self, header):
        return self.calculate_array_x_start_index(header) + header.NUM_ELEMENTS * 8

    def calculate_array_z_start_index(self, header):
        return self.calculate_array_y_start_index(header) + header.NUM_ELEMENTS * 8

    def calculate_frequencies_start_index(self, header):
        return self.calculate_array_z_start_index(header) + header.NUM_ELEMENTS * 8

    def calculate_element_mask_start_index(self, header):
        return (
            self.calculate_frequencies_start_index(header) + header.NUM_FREQUENCIES * 8
        )

    def calculate_element_weight_start_index(self, header):
        return self.calculate_element_mask_start_index(header) + header.NUM_ELEMENTS * 1

    def calculate_thetas_start_index(self, header):
        return (
            self.calculate_element_weight_start_index(header) + header.NUM_ELEMENTS * 8
        )

    def calculate_phis_start_index(self, header):
        return (
            self.calculate_thetas_start_index(header)
            + header.NUM_THETAS * header.INDEX_SIZE
        )

    def calculate_data_start_index(self, header):
        return (
            self.calculate_phis_start_index(header)
            + header.NUM_PHIS * header.INDEX_SIZE
        )

    def calculate_index_dtype(self, header):
        if header.INDEX_SIZE == 1:
            return np.uint8
        if header.INDEX_SIZE == 2:
            return np.uint16
        if header.INDEX_SIZE == 4:
            return np.float32
        if header.INDEX_SIZE == 8:
            return np.float64

    def needs_byte_swap(self, header):
        swap = False
        sys_endian = sys.byteorder
        if sys_endian == "little":
            data_endian = "<"
        else:
            data_endian = ">"
        if not chr(header.ENDIAN) == data_endian:
            if (chr(header.ENDIAN) == "<" and data_endian == ">") or (
                chr(header.ENDIAN) == ">" and data_endian == "<"
            ):
                swap = True
            else:
                print(
                    "Unrecognized endian combination: "
                    + repr(header.ENDIAN)
                    + " "
                    + repr(data_endian)
                )
        return swap

    def decode_data(self, data, header):
        d = data[self.calculate_data_start_index(header) :]
        print(len(d))
        data_array = numpy.frombuffer(d, dtype=np.float64)
        data_array = data_array.reshape(header.NUM_THETAS, header.NUM_PHIS, -1)
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_thetas(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_thetas_start_index(
                    header
                ) : self.calculate_phis_start_index(header)
            ],
            dtype=self.calculate_index_dtype(header),
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_phis(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_phis_start_index(
                    header
                ) : self.calculate_data_start_index(header)
            ],
            dtype=self.calculate_index_dtype(header),
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_frequencies(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_frequencies_start_index(
                    header
                ) : self.calculate_element_mask_start_index(header)
            ],
            dtype=np.double,
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_array_x(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_array_x_start_index(
                    header
                ) : self.calculate_array_y_start_index(header)
            ],
            dtype=np.double,
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_array_y(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_array_y_start_index(
                    header
                ) : self.calculate_array_z_start_index(header)
            ],
            dtype=np.double,
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_array_z(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_array_z_start_index(
                    header
                ) : self.calculate_frequencies_start_index(header)
            ],
            dtype=np.double,
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_element_mask(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_element_mask_start_index(
                    header
                ) : self.calculate_element_weight_start_index(header)
            ],
            dtype=np.uint8,
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def decode_element_weights(self, data, header):
        data_array = numpy.frombuffer(
            data[
                self.calculate_element_weight_start_index(
                    header
                ) : self.calculate_thetas_start_index(header)
            ],
            dtype=np.double,
        )
        if self.needs_byte_swap(header):
            data_array = data_array.byteswap()
        return data_array

    def is_start_packet(self, data):
        return (
            data[0] == ord("A")
            and data[1] == ord("C")
            and data[2] == ord("B")
            and data[3] == ord("R")
        )

    def is_continued_packet(self, data):
        return (
            data[0] == ord("A")
            and data[1] == ord("C")
            and data[2] == ord("B")
            and data[3] == ord("C")
        )

    def get_start_payload(self, data):
        header = self.decode_header(data)
        d = data[self.header_length_b :]
        return d

    def get_continued_payload(self, data):
        header = self.decode_continued_header(data)
        d = data[self.header_contd_length_b :]
        return d

    def get_packet_num(self, data):
        header = self.decode_header(data)
        return header.PACKET_NUM

    def get_num_packets(self, data):
        header = self.decode_header(data)
        return header.NUM_PACKETS

    def get_continued_packet_num(self, data):
        header = self.decode_continued_header(data)
        return header.PACKET_NUM

    def get_continued_subpacket_index(self, data):
        header = self.decode_continued_header(data)
        return header.SUB_PACKET_INDEX

    def decode(self, data):
        header = self.decode_header(data)
        d = self.decode_data(data, header)
        thetas = self.decode_thetas(data, header)
        phis = self.decode_phis(data, header)
        frequencies = self.decode_frequencies(data, header)

        array_x = self.decode_array_x(data, header)
        array_y = self.decode_array_y(data, header)
        array_z = self.decode_array_z(data, header)

        window_length_s = header.WINDOW_LENGTH_S
        sample_rate = header.SAMPLE_RATE

        element_mask = self.decode_element_mask(data, header)
        mode = header.MODE
        weighting_type = header.WEIGHTING_TYPE
        xform_pitch = header.XFORM_PITCH
        xform_roll = header.XFORM_ROLL
        xform_yaw = header.XFORM_YAW

        element_weights = self.decode_element_weights(data, header)

        dc = DataContainer_Beamformed_Output_Raw(
            data=d,
            thetas=thetas,
            phis=phis,
            frequencies=frequencies,
            start_time=np.datetime64(header.START_TIME, "ns"),
            array_x=array_x,
            array_y=array_y,
            array_z=array_z,
            window_length_s=window_length_s,
            sample_rate=sample_rate,
            element_mask=element_mask,
            mode=mode,
            weighting_type=self.weight_type_lookup[weighting_type.decode()],
            xform_pitch=xform_pitch,
            xform_roll=xform_roll,
            xform_yaw=xform_yaw,
            element_weights=element_weights,
        )
        print("data shape " + repr(dc.data.shape))
        print(header)
        return dc

    def encode(
        self,
        data_array,
        bearings,
        elevations,
        start_time,
        frequencies,
        array_x,
        array_y,
        array_z,
        element_mask,
        element_weights,
        sample_rate,
        window_length_s,
        pitch,
        roll,
        yaw,
        mode,
        weighting_type,
        packet_num,
    ):
        frame_start_time = start_time.astype(">i8")
        num_elements = len(array_x)
        data_endian = data_array.dtype.byteorder
        if data_endian == "=":  # system order:
            sys_endian = sys.byteorder
            if sys_endian == "little":
                data_endian = "<"
            else:
                data_endian = ">"
        # TODO: How to make work if split accross multiple frames
        MAX_UDP_SIZE = 65507

        data_payload = (
            array_x.tobytes()
            + array_y.tobytes()
            + array_z.tobytes()
            + frequencies.tobytes()
            + element_mask.tobytes()
            + element_weights.tobytes()
            + bearings.tobytes()
            + elevations.tobytes()
            + data_array.tobytes()
        )

        payload_length = len(data_payload)
        num_sub_packets = 1
        if payload_length > MAX_UDP_SIZE - self.header_length_b:
            # single packet
            excess_length = payload_length - (MAX_UDP_SIZE - self.header_length_b)
            data_per_contd_packet = MAX_UDP_SIZE - self.header_contd_length_b
            num_sub_packets = 1 + math.ceil(excess_length / data_per_contd_packet)

        weight_type = bytes(self.weight_type_reverse_lookup[weighting_type], "utf-8")
        header = struct.pack(
            self.header_fmt,
            ord("A"),
            ord("C"),
            ord("B"),
            ord("R"),
            self.version_major,
            self.version_minor,
            ord(data_endian),
            num_elements,
            len(frequencies),
            len(bearings),
            len(elevations),
            bearings.dtype.itemsize,
            data_array.dtype.itemsize,
            sample_rate,
            window_length_s,
            frame_start_time,
            pitch,
            roll,
            yaw,
            bytes("R", "utf-8"),  #'M'.decode('ascii'),#ord(mode[0]),
            weight_type,  # ?'.decode('ascii'),#ord(weighting_type[0]),
            num_sub_packets,
            packet_num,
        )
        data_to_send = []
        if num_sub_packets == 1:
            data_to_send.append(header + data_payload)
        else:
            start_ind = MAX_UDP_SIZE - self.header_length_b
            data_to_send.append(header + data_payload[:start_ind])
            for ind in range(1, num_sub_packets):
                header = struct.pack(
                    self.header_contd_fmt,
                    ord("A"),
                    ord("C"),
                    ord("B"),
                    ord("C"),
                    ind,
                    packet_num,
                )
                end_ind = min(payload_length, start_ind + data_per_contd_packet)
                data_to_send.append(header + data_payload[start_ind:end_ind])
                start_ind = end_ind
        return data_to_send
