try:
    import acbotics_interface_ext as ac
except ModuleNotFoundError:
    import acbotics_interface as ac
from acbotics_pipeline.fixtures.fixture_pyplot import Fixture_Pyplot

from acbotics_pipeline.blocks.cpp_interface.pts_to_data_container import (
    Pts_To_Data_Container,
)

from acbotics_pipeline.blocks.cpp_interface.ept_to_data_container import (
    Ept_To_Data_Container,
)

from acbotics_pipeline.blocks.cpp_interface.bno_to_data_container import (
    Bno_To_Data_Container,
)

from acbotics_pipeline.blocks.cpp_interface.bnr_to_data_container import (
    Bnr_To_Data_Container,
)

from acbotics_pipeline.blocks.cpp_interface.rtc_to_data_container import (
    Rtc_To_Data_Container,
)


from acbotics_pipeline.blocks.cpp_interface.imu_to_data_container import (
    Imu_To_Data_Container,
)
from acbotics_pipeline.blocks.output.pyplot.out_pyplot_sensor import (
    Out_Pyplot_Sensor,
)


class Fixture_CPP_Demo(Fixture_Pyplot):

    def __init__(self, args):
        self.args = args
        super().__init__()

    def build(self):
        self.add_cpp_block(
            "SENSE_IN",
            ac.UdpSocketIn(
                self.args.use_mcast,
                self.args.iface_ip,
                self.args.sen_port,
                self.args.mcast_group,
            ),
        )
        test_queue = ac.Q_PTS.create()
        self.translate_block = Pts_To_Data_Container(test_queue)
        self.cpp_blocks["SENSE_IN"].register_client_pts(test_queue)
        self.add_block(self.translate_block, output_signal="PTS")
        self.add_block(
            Out_Pyplot_Sensor(
                update_rate=1,
                samples_to_plot=100,
                figure_num=self.get_next_fig_num(),
                title="PTS In",
                ymin=0,
                ymax=100,
            ),
            input_signal="PTS",
        )

        test_queue_imu = ac.Q_IMU.create()
        self.translate_block_imu = Imu_To_Data_Container(test_queue_imu)
        self.cpp_blocks["SENSE_IN"].register_client_imu(test_queue_imu)
        self.add_block(self.translate_block_imu, output_signal="IMU")
        self.add_block(
            Out_Pyplot_Sensor(
                update_rate=1,
                samples_to_plot=100,
                figure_num=self.get_next_fig_num(),
                title="IMU",
                ymin=0,
                ymax=100,
            ),
            input_signal="IMU",
        )

        test_queue_ept = ac.Q_EPT.create()
        self.translate_block_ept = Ept_To_Data_Container(test_queue_ept)
        self.cpp_blocks["SENSE_IN"].register_client_ept(test_queue_ept)
        self.add_block(self.translate_block_ept, output_signal="EPT")
        self.add_block(
            Out_Pyplot_Sensor(
                update_rate=1,
                samples_to_plot=100,
                figure_num=self.get_next_fig_num(),
                title="EPT",
                ymin=0,
                ymax=100,
            ),
            input_signal="EPT",
        )

        test_queue_bno = ac.Q_BNO.create()
        self.translate_block_bno = Bno_To_Data_Container(test_queue_bno)
        self.cpp_blocks["SENSE_IN"].register_client_bno(test_queue_bno)
        self.add_block(self.translate_block_bno)
        accel_plot = Out_Pyplot_Sensor(
            update_rate=1,
            samples_to_plot=100,
            figure_num=self.get_next_fig_num(),
            title="Accel",
            ymin=0,
            ymax=100,
        )
        self.add_block(accel_plot)
        self.translate_block_bno.add_acceleration_callback(accel_plot.input_data)

        gyro_plot = Out_Pyplot_Sensor(
            update_rate=1,
            samples_to_plot=100,
            figure_num=self.get_next_fig_num(),
            title="Gyro",
            ymin=0,
            ymax=100,
        )
        self.add_block(gyro_plot)
        self.translate_block_bno.add_gyro_callback(gyro_plot.input_data)

        mag_plot = Out_Pyplot_Sensor(
            update_rate=1,
            samples_to_plot=100,
            figure_num=self.get_next_fig_num(),
            title="Mag",
            ymin=0,
            ymax=100,
        )
        self.add_block(mag_plot)
        self.translate_block_bno.add_magnetic_callback(mag_plot.input_data)

        test_queue_bnr = ac.Q_BNR.create()
        self.translate_block_bnr = Bnr_To_Data_Container(test_queue_bnr)
        self.cpp_blocks["SENSE_IN"].register_client_bnr(test_queue_bnr)
        self.add_block(self.translate_block_bnr, output_signal="BNR")
        self.add_block(
            Out_Pyplot_Sensor(
                update_rate=1,
                samples_to_plot=100,
                figure_num=self.get_next_fig_num(),
                title="BNR",
                ymin=0,
                ymax=100,
            ),
            input_signal="BNR",
        )

        test_queue_rtc = ac.Q_RTC.create()
        self.translate_block_rtc = Rtc_To_Data_Container(test_queue_rtc)
        self.cpp_blocks["SENSE_IN"].register_client_rtc(test_queue_rtc)
        self.add_block(self.translate_block_rtc, output_signal="RTC")
        self.add_block(
            Out_Pyplot_Sensor(
                update_rate=1,
                samples_to_plot=100,
                figure_num=self.get_next_fig_num(),
                title="RTC",
                ymin=0,
                ymax=100,
            ),
            input_signal="RTC",
        )


if __name__ == "__main__":
    import argparse

    print("Hello")
    parser = argparse.ArgumentParser(
        prog="Acbotics Dashboard",
        description="Launch a graphical display to visualize AcSense data streams",
        epilog="Written by Acbotics Research",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--iface_ip",
        type=str,
        default="127.0.0.1",
        help="IP of interface to bind, on host",
    )
    parser.add_argument("--use_mcast", action="store_true")
    parser.add_argument(
        "--mcast_group",
        type=str,
        default="224.1.1.1",
        help="Multicast group to collect data from (if using multicast)",
    )
    parser.add_argument(
        "--aco_port",
        type=int,
        default=9760,
        help="Port to collect acoustic data from",
    )
    parser.add_argument(
        "--sen_port",
        type=int,
        default=9770,
        help="Port to collect internal sensor data from",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Array & beamformer configuration file (YAML)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        type=int,
        default=0,
        help="Set log verbosity level",
    )
    parser.add_argument(
        "--debug_python",
        "-d",
        action="store_true",
        help="Enable expanded debug of the Python code for this app",
    )
    parser.add_argument(
        "--debug_interface_helper",
        action="store_true",
        help="Enable expanded debug for Interface Helper",
    )
    parser.add_argument(
        "--debug_interface_helper_ext",
        action="store_true",
        help="Enable expanded debug for Interface Helper Extension",
    )
    parser.add_argument(
        "--debug_socket_in",
        action="store_true",
        help="Enable expanded debug for UdpSocketIn",
    )
    parser.add_argument(
        "--debug_beamformer",
        action="store_true",
        help="Enable expanded debug for Beamformer",
    )
    parser.add_argument(
        "--debug_udp_data",
        action="store_true",
        help="Enable expanded debug for UdpData",
    )
    parser.add_argument(
        "--debug_fft", action="store_true", help="Enable expanded debug for FFT"
    )

    args, unk = parser.parse_known_args()
    print(f"Using arguments : \n{args.__dict__}")
    if len(unk) > 0:
        print(f"Unknown args ignored : {unk}")

    f = Fixture_CPP_Demo(args)
    f.run()
