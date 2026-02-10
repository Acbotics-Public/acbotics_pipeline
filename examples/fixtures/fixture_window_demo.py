try:
    import acbotics_interface_ext as ac
except ModuleNotFoundError:
    import acbotics_interface as ac
from acbotics_pipeline.fixtures.fixture_pyplot import Fixture_Pyplot

from acbotics_pipeline.blocks.cpp_interface import (
    Pts_To_Data_Container,
    Ept_To_Data_Container,
    Bno_To_Data_Container,
    Bnr_To_Data_Container,
    Rtc_To_Data_Container,
    Imu_To_Data_Container,
    Aco_To_Data_Container,
)

from acbotics_pipeline.blocks.processes.routing.pr_window import Pr_Window
from acbotics_pipeline.blocks.output.pyplot import (
    Out_Pyplot_Sensor,
    Out_Pyplot_Window,
    Out_Pyplot_Time_Series_Multiple,
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

        self.add_cpp_block(
            "ACO_IN",
            ac.UdpSocketIn(
                self.args.use_mcast,
                self.args.iface_ip,
                self.args.aco_port,
                self.args.mcast_group,
            ),
        )
        test_queue_aco = ac.Q_ACO.create()
        self.translate_block_aco = Aco_To_Data_Container(test_queue_aco)
        self.cpp_blocks["ACO_IN"].register_client_aco(test_queue_aco)
        self.add_block(self.translate_block_aco, output_signal="ACO")

        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=52734,
                figure_num=self.get_next_fig_num(),
                title="Data In",
                num_sigs=8,
                ymin=-(2**15),
                ymax=2**15,
            ),
            input_signal="ACO",
        )

        test_queue = ac.Q_PTS.create()
        self.translate_block = Pts_To_Data_Container(test_queue)
        self.cpp_blocks["SENSE_IN"].register_client_pts(test_queue)
        self.add_block(self.translate_block, output_signal="PTS")

        test_queue_imu = ac.Q_IMU.create()
        self.translate_block_imu = Imu_To_Data_Container(test_queue_imu)
        self.cpp_blocks["SENSE_IN"].register_client_imu(test_queue_imu)
        self.add_block(self.translate_block_imu, output_signal="IMU")

        test_queue_ept = ac.Q_EPT.create()
        self.translate_block_ept = Ept_To_Data_Container(test_queue_ept)
        self.cpp_blocks["SENSE_IN"].register_client_ept(test_queue_ept)
        self.add_block(self.translate_block_ept, output_signal="EPT")

        test_queue_bno = ac.Q_BNO.create()
        self.translate_block_bno = Bno_To_Data_Container(test_queue_bno)
        self.cpp_blocks["SENSE_IN"].register_client_bno(test_queue_bno)
        self.add_block(self.translate_block_bno)
        # self.translate_block_bno.add_acceleration_callback(accel_plot.input_data)

        # self.translate_block_bno.add_gyro_callback(gyro_plot.input_data)

        # self.translate_block_bno.add_magnetic_callback(mag_plot.input_data)

        test_queue_bnr = ac.Q_BNR.create()
        self.translate_block_bnr = Bnr_To_Data_Container(test_queue_bnr)
        self.cpp_blocks["SENSE_IN"].register_client_bnr(test_queue_bnr)
        self.add_block(self.translate_block_bnr, output_signal="BNR")

        test_queue_rtc = ac.Q_RTC.create()
        self.translate_block_rtc = Rtc_To_Data_Container(test_queue_rtc)
        self.cpp_blocks["SENSE_IN"].register_client_rtc(test_queue_rtc)
        self.add_block(self.translate_block_rtc, output_signal="RTC")

        window_block = Pr_Window(
            window_length_sec=11, overlap_sec=1, sensor_names=["IMU"]
        )
        self.add_block(
            window_block,
            input_signal="ACO",
            output_signal="WIN",
        )
        self.translate_block_imu.add_callback(window_block.get_sensor_callback("IMU"))

        self.add_block(
            Out_Pyplot_Window(update_rate=2, figure_num=2), input_signal="WIN"
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
