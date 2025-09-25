import fixture
import fixture_pyplot

# from blocks.input.network.in_socket_udp_constant_rate_process import In_Socket_UDP_Constant_Rate_Process
from blocks.input.network.in_socket_udp_constant_rate_process_ac_sense import (
    In_Socket_UDP_Constant_Rate_Process_Ac_Sense,
)
from blocks.input.network.in_socket_udp_beamform_2d import In_Socket_UDP_Beamform_2D

from blocks.processes.math.pr_to_int16 import Pr_To_Int16
from blocks.processes.math.pr_to_float32 import Pr_To_Float32
from blocks.processes.math.pr_gain import Pr_Gain
from blocks.processes.filters.pr_lowpass_butter import Pr_Lowpass_Butter


from blocks.output.file.out_csv_file import Out_CSV_File
from blocks.output.pyplot.out_pyplot_time_series_multiple import (
    Out_Pyplot_Time_Series_Multiple,
)
from blocks.output.pyplot.out_pyplot_beamformed_data_3d import (
    Out_Pyplot_Beamformed_Data_3D,
)
from blocks.output.pyplot.out_pyplot_spectrogram_queue import Out_Pyplot_Spectrogram
from blocks.output.pyplot.out_pyplot_spectrum import Out_Pyplot_Spectrum
import time
import numpy as np


class Fixture_UDP_Receiver(fixture_pyplot.Fixture_Pyplot):
    def build(self):
        start_time = np.datetime64(time.time_ns(), "ns")
        SAMPLE_RATE = 52768
        num_sigs = 16
        # target_ip_addr = "10.42.0.115" #'localhost'
        # target_ip_addr = "192.168.1.32"
        # #target_ip_addr = '192.168.7.1'
        # multicast = False
        target_ip_addr = "224.1.1.1"
        multicast = True
        self.add_block(
            In_Socket_UDP_Constant_Rate_Process_Ac_Sense(
                target_ip_addr, port=9760, multicast=multicast
            ),
            output_signal="UDP_OUT",
        )

        # self.add_block(In_Socket_UDP_Constant_Rate(target_ip_addr,
        #                                            port = 8091),
        #                output_signal = "UDP_OUT_2")
        self.add_block(
            Pr_To_Int16(), input_signal="UDP_OUT", output_signal="UDP_SIGNED"
        )
        self.add_block(
            Pr_To_Float32(), input_signal="UDP_SIGNED", output_signal="UDP_FLOAT"
        )
        self.add_block(
            Pr_Gain(gain=1.0 / 2**16 * 2.5),
            input_signal="UDP_FLOAT",
            output_signal="UDP_SCALED",
        )

        # self.add_block(Pr_Lowpass_Butter(order=4, cutoff_frequency=50, sample_rate=1000),
        #                input_signal="UDP_FLOAT",
        #                output_signal="UDP_FILTERED")

        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=SAMPLE_RATE,
                figure_num=4,
                title="DAQ UDP 0,1,2,4",
                ymin=-(2**15),
                ymax=2**15,
                num_sigs=num_sigs,
                channels=[0, 1, 2, 3],
            ),
            input_signal="UDP_FLOAT",
        )

        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=SAMPLE_RATE,
                figure_num=5,
                title="DAQ UDP 4,5,6,7",
                ymin=-(2**15),
                ymax=2**15,
                num_sigs=num_sigs,
                channels=[4, 5, 6, 7],
            ),
            input_signal="UDP_FLOAT",
        )

        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=SAMPLE_RATE,
                figure_num=6,
                title="DAQ UDP 8,9,10,11",
                ymin=-(2**15),
                ymax=2**15,
                num_sigs=num_sigs,
                channels=[8, 9, 10, 11],
            ),
            input_signal="UDP_FLOAT",
        )

        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=SAMPLE_RATE,
                figure_num=7,
                title="DAQ UDP 12,13,14,15",
                ymin=-(2**15),
                ymax=2**15,
                num_sigs=num_sigs,
                channels=[12, 13, 14, 15],
            ),
            input_signal="UDP_FLOAT",
        )

        # self.add_block(Out_Pyplot_Time_Series_Multiple(update_rate=1,
        #                                                samples_to_plot=SAMPLE_RATE,
        #                                                figure_num = 5,
        #                                                title="DAQ UDP 1",
        #                                                ymin = -2**11,
        #                                                ymax = 2**11,
        #                                                num_sigs=num_sigs,
        #                                                channels = [1]),
        #                input_signal = "UDP_FLOAT")
        # self.add_block(Out_Pyplot_Time_Series_Multiple(update_rate=1,
        #                                                samples_to_plot=SAMPLE_RATE,
        #                                                figure_num = 6,
        #                                                title="DAQ UDP 2",
        #                                                ymin = -2**11,
        #                                                ymax = 2**11,
        #                                                num_sigs=num_sigs,
        #                                                channels = [2]),
        #                input_signal = "UDP_FLOAT")

        #
        # self.add_block(In_Socket_UDP_Constant_Rate_Process(target_ip_addr,
        #                                            port = 8095,
        #                                            multicast=multicast),
        #                output_signal = "UDP_OUT2")
        # self.add_block(Out_Pyplot_Spectrogram(
        #                                       update_rate = 1,
        #                                       samples_to_use = SAMPLE_RATE,
        #                                       figure_num = 7,
        #                                       ymin=0.0000000000001,
        #                                       #ymin=0.000000000000001,
        #                                       ymax= 1,
        #                                       num_sigs = num_sigs,
        #                                       channel = 2),
        #                input_signal = "UDP_SCALED")

        # self.add_block(Out_Pyplot_Spectrum(
        #     update_rate=1,
        #     samples_to_use=SAMPLE_RATE,
        #     figure_num=6,
        #     log_y= False,
        #     num_sigs= num_sigs,
        #     channels = [0],
        #     ymax = 0.4
        #     ),
        #     input_signal = "UDP_SCALED")

        # self.add_block(Out_CSV_File(filename = "moore_debug_9.csv",
        #                             num_decimals=8),
        #                 input_signal = "UDP_SIGNED")
        # self.add_block(In_Socket_UDP_Constant_Rate(target_ip_addr,
        #                                            port = 8091),
        #                output_signal = "UDP_OUT_2")

        # self.add_block(Out_Pyplot_Time_Series_Multiple(update_rate=1,
        #                                                samples_to_plot=SAMPLE_RATE,
        #                                                figure_num = 5,
        #                                                title="DAQ UDP 2",
        #                                                ymin = 0,
        #                                                ymax = 2**16,
        #                                                num_sigs=num_sigs),
        #                input_signal = "UDP_OUT2")

        # self.add_block(Out_Pyplot_Time_Series_Multiple(update_rate=1,
        #                                                samples_to_plot=SAMPLE_RATE,
        #                                                figure_num = 5,
        #                                                title="DAQ UDP 2",
        #                                                ymin = 0,
        #                                                ymax = 2**16,
        #                                                num_sigs=2),
        #                input_signal = "UDP_OUT_2")


#        self.add_block(In_Socket_UDP_Beamform_2D(target_ip_addr,
#                                                   port = 8090),
#                       output_signal = "UDP_BEAMFORM_OUT")

#        self.add_block(Out_Pyplot_Beamformed_Data_3D(update_rate=1,
#                                                     figure_num = 5,
#                                                     title="DAQ BEAMFORM UDP"),
#                       input_signal = "UDP_BEAMFORM_OUT")


if __name__ == "__main__":
    f = Fixture_UDP_Receiver()
    f.run()
