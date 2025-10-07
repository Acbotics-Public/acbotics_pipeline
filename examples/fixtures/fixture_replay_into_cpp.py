try:
    import acbotics_interface_ext as ac
except ModuleNotFoundError:
    import acbotics_interface as ac
from acbotics_pipeline.fixtures.fixture_pyplot import Fixture_Pyplot

from acbotics_pipeline.blocks.cpp_interface.aco_to_data_container import (
    Aco_To_Data_Container,
)

from acbotics_pipeline.blocks.cpp_interface.data_container_to_aco import (
    Data_Container_To_ACO,
)

from acbotics_pipeline.blocks.output.pyplot.out_pyplot_time_series_multiple import (
    Out_Pyplot_Time_Series_Multiple,
)

from acbotics_pipeline.blocks.output.pyplot.out_pyplot_spectrogram import (
    Out_Pyplot_Spectrogram,
)
from acbotics_pipeline.blocks.cpp_interface.fft_to_data_container import (
    FFT_To_Data_Container,
)

from acbotics_pipeline.blocks.input.generator.in_exponential_sweep import (
    In_Exponential_Sweep,
)
from acbotics_pipeline.blocks.output.pyplot.out_pyplot_spectrum_fft import (
    Out_Pyplot_Spectrum_FFT,
)

import numpy as np
import time


class Fixture_Replay_Into_Cpp(Fixture_Pyplot):
    def build(self):
        # create signal
        self.add_block(
            In_Exponential_Sweep(
                start_frequency=100,
                stop_frequency=10000,
                amplitude=3000,
                sweep_time=5,
                period=10,
                sample_rate=52000,
                start_time=np.datetime64(time.time_ns(), "ns"),
                output_batch_size=52000,
            ),
            output_signal="SWEEP",
        )
        # create cpp queue to pass into
        in_queue = ac.Q_ACO.create()
        self.translate_in_block = Data_Container_To_ACO(in_queue)
        self.add_block(self.translate_in_block, input_signal="SWEEP")

        # pass back out to python
        self.translate_block = Aco_To_Data_Container(in_queue)
        self.add_block(self.translate_block, output_signal="ACO")

        # plot time series directly and s spectrogram
        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=52734,
                figure_num=self.get_next_fig_num(),
                title="Data In",
                num_sigs=1,
                ymin=-(2**15),
                ymax=2**15,
            ),
            input_signal="ACO",
        )
        self.add_block(
            Out_Pyplot_Spectrogram(
                update_rate=1,
                samples_to_use=52000,
                figure_num=self.get_next_fig_num(),
                title="Exponential Sweep",
                ymin=0.1,
                ymax=1000,
            ),
            input_signal="ACO",
        )

        # create a cpp FFT block
        self.fft_block = ac.FFT.create()
        self.add_cpp_block("FFT", self.fft_block)
        # connect the signal to the FFT block
        self.translate_in_block2 = Data_Container_To_ACO(
            self.fft_block.get_input_queue()
        )
        self.add_block(self.translate_in_block2, input_signal="SWEEP")

        # get the fft from cpp back to python
        self.translate_block2 = FFT_To_Data_Container()
        self.fft_block.register_client(self.translate_block2.cpp_queue_fft)
        self.add_block(self.translate_block2, output_signal="FFT")

        # plot the cpp fft as a spectrum
        self.add_block(
            Out_Pyplot_Spectrum_FFT(
                update_rate=1,
                figure_num=self.get_next_fig_num(),
                title="CPP FFT",
                ymin=0,
                ymax=0.05,
            ),
            input_signal="FFT",
        )


if __name__ == "__main__":
    f = Fixture_Replay_Into_Cpp()
    f.run()
