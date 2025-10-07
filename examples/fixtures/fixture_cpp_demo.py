try:
    import acbotics_interface_ext as ac
except ModuleNotFoundError:
    import acbotics_interface as ac
from acbotics_pipeline.fixtures.fixture_pyplot import Fixture_Pyplot

from acbotics_pipeline.blocks.cpp_interface.aco_to_data_container import (
    Aco_To_Data_Container,
)
from acbotics_pipeline.blocks.output.pyplot.out_pyplot_time_series_multiple import (
    Out_Pyplot_Time_Series_Multiple,
)


class Fixture_CPP_Demo(Fixture_Pyplot):

    def __init__(self, args):
        self.args = args
        super().__init__()

    def build(self):
        self.add_cpp_block(
            "ACO_IN",
            ac.UdpSocketIn(
                self.args.use_mcast,
                self.args.iface_ip,
                self.args.aco_port,
                self.args.mcast_group,
            ),
        )
        test_queue = ac.Q_ACO.create()
        self.translate_block = Aco_To_Data_Container(test_queue)
        self.cpp_blocks["ACO_IN"].register_client_aco(test_queue)
        self.add_block(self.translate_block, output_signal="ACO")
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
