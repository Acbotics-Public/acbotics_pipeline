try:
    import acbotics_interface_ext as ac
except ModuleNotFoundError:
    import acbotics_interface as ac
from acbotics_pipeline.fixtures import Fixture

from acbotics_pipeline.blocks.cpp_interface.aco_to_data_container import (
    Aco_To_Data_Container,
)
import os

class Fixture_CPP_Demo(Fixture):

    def __init__(self, args):
        self.args = args
        super().__init__()

    def configure_logger_outdir(self):
        outdir = os.path.expanduser("~/acsense_data/")
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        self.outdir = outdir

        self.cpp_blocks["ACO_LOG"].set_outdir(outdir)
        self.cpp_blocks["SENSE_LOG"].set_outdir(outdir)


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

        self.add_cpp_block(
            "SENSE_IN",
            ac.UdpSocketIn(
                args.use_mcast, args.iface_ip, args.sen_port, args.mcast_group
            ),
        )

        self.add_cpp_block("ACO_LOG", ac.LoggerBlock())
        self.cpp_blocks["ACO_IN"].register_client_aco(
            self.cpp_blocks["ACO_LOG"].get_input_queue()
        )

        self.add_cpp_block("SENSE_LOG", ac.Logger_Sensor_Block())
        self.cpp_blocks["SENSE_IN"].register_client(self.cpp_blocks["SENSE_LOG"])


        self.configure_logger_outdir()

        self.cpp_blocks["ACO_LOG"].start_logging()
        self.cpp_blocks["SENSE_LOG"].start_logging()



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
        "--verbose",
        "-v",
        type=int,
        default=0,
        help="Set log verbosity level",
    )
    args, unk = parser.parse_known_args()
    print(f"Using arguments : \n{args.__dict__}")
    if len(unk) > 0:
        print(f"Unknown args ignored : {unk}")

    f = Fixture_CPP_Demo(args)
    f.run()
