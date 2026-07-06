from acbotics_pipeline.fixtures import Fixture_Pyplot

from acbotics_pipeline.blocks.input.network import (
    In_Socket_UDP_Constant_Rate_Process_Ac_Sense,
    In_Socket_UDP_Beamform_2D,
)

from acbotics_pipeline.blocks.processes.math import Pr_To_Int16, Pr_To_Float32, Pr_Gain


from acbotics_pipeline.blocks.output.file import Out_CSV_File


from acbotics_pipeline.blocks.output.pyplot import (
    Out_Pyplot_Time_Series_Multiple,
    Out_Pyplot_Beamformed_Data_3D,
    Out_Pyplot_Spectrogram,
    Out_Pyplot_Spectrum,
)
import time
import numpy as np


class Fixture_UDP_Receiver(Fixture_Pyplot):
    def build(self):
        start_time = np.datetime64(time.time_ns(), "ns")
        SAMPLE_RATE = 52768
        num_sigs = 16
        iface_ip = "127.0.0.1"
        multicast_group = "224.1.1.1"
        multicast = True
        self.add_block(
            In_Socket_UDP_Constant_Rate_Process_Ac_Sense(
                iface_ip,
                port=9760,
                multicast=multicast,
                # multicast_interface=args.gps_iface_ip,
                multicast_group=multicast_group,
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


if __name__ == "__main__":
    f = Fixture_UDP_Receiver()
    f.run()
