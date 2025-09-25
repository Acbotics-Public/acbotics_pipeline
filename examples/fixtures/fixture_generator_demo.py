from acbotics_pipeline.blocks.input.file.in_wav_file import In_Wav_File
from acbotics_pipeline.blocks.input.generator.in_sine import In_Sine
from acbotics_pipeline.blocks.input.generator.in_linear_sweep import In_Linear_Sweep
from acbotics_pipeline.blocks.input.generator.in_exponential_sweep import (
    In_Exponential_Sweep,
)
from acbotics_pipeline.blocks.input.generator.in_square import In_Square
from acbotics_pipeline.blocks.input.generator.in_triangle import In_Triangle
from acbotics_pipeline.blocks.input.generator.in_sawtooth import In_Sawtooth

from acbotics_pipeline.blocks.output.pyplot.out_pyplot_time_series_multiple import (
    Out_Pyplot_Time_Series_Multiple,
)
from acbotics_pipeline.blocks.output.pyplot.out_pyplot_spectrum import (
    Out_Pyplot_Spectrum,
)
from acbotics_pipeline.blocks.output.pyplot.out_pyplot_spectrogram import (
    Out_Pyplot_Spectrogram,
)

from acbotics_pipeline.blocks.processes.math.pr_noise_gaussian import Pr_Noise_Gaussian

from acbotics_pipeline.fixtures.fixture_pyplot import Fixture_Pyplot

import time
import numpy as np


class Fixture_Test_Blocks(Fixture_Pyplot):
    def __init(self):
        super().__init__()

    def build(self):
        SAMPLE_RATE = 25000
        # Exponential Sweep
        self.add_block(
            In_Exponential_Sweep(
                start_frequency=100,
                stop_frequency=10000,
                amplitude=3000,
                sweep_time=5,
                period=10,
                sample_rate=SAMPLE_RATE,
                start_time=np.datetime64(time.time_ns(), "ns"),
                output_batch_size=SAMPLE_RATE,
            ),
            output_signal="SWEEP",
        )
        self.add_block(
            Pr_Noise_Gaussian(100), input_signal="SWEEP", output_signal="NOISY_SWEEP"
        )
        self.add_block(
            Out_Pyplot_Time_Series_Multiple(
                update_rate=1,
                samples_to_plot=SAMPLE_RATE,
                figure_num=self.get_next_fig_num(),
                title="Exponential Sweep Time Series",
                ymin=-4000,
                ymax=4000,
            ),
            input_signal="NOISY_SWEEP",
        )
        self.add_block(
            Out_Pyplot_Spectrum(
                update_rate=1,
                samples_to_use=SAMPLE_RATE,
                figure_num=self.get_next_fig_num(),
                title="Exponential Sweep Spectrum",
                ymin=0,
                ymax=500,
            ),
            input_signal="NOISY_SWEEP",
        )
        self.add_block(
            Out_Pyplot_Spectrogram(
                update_rate=1,
                samples_to_use=SAMPLE_RATE,
                figure_num=self.get_next_fig_num(),
                title="Exponential Sweep",
                ymin=0.1,
                ymax=1000,
            ),
            input_signal="NOISY_SWEEP",
        )

        # # Linear Sweep
        # self.add_block(
        #     In_Linear_Sweep(
        #         start_frequency=100,
        #         stop_frequency=10000,
        #         amplitude=3000,
        #         sweep_time=5,
        #         period=10,
        #         sample_rate=SAMPLE_RATE,
        #         start_time=np.datetime64(time.time_ns(), "ns"),
        #         output_batch_size=SAMPLE_RATE,
        #     ),
        #     output_signal="LINEAR_SWEEP",
        # )
        # self.add_block(
        #     Pr_Noise_Gaussian(100),
        #     input_signal="SWEEP",
        #     output_signal="NOISY_LINEAR_SWEEP",
        # )
        # self.add_block(
        #     Out_Pyplot_Time_Series_Multiple(
        #         update_rate=1,
        #         samples_to_plot=SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Linear Sweep Time Series",
        #         ymin=-4000,
        #         ymax=4000,
        #     ),
        #     input_signal="NOISY_LINEAR_SWEEP",
        # )
        # self.add_block(
        #     Out_Pyplot_Spectrum(
        #         update_rate=1,
        #         samples_to_use=SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Linear Sweep Spectrum",
        #         ymin=0,
        #         ymax=4000,
        #     ),
        #     input_signal="NOISY_LINEAR_SWEEP",
        # )
        # self.add_block(
        #     Out_Pyplot_Spectrogram(
        #         update_rate=1,
        #         samples_to_use=SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Linear Sweep",
        #         ymin=0.1,
        #         ymax=1000,
        #     ),
        #     input_signal="NOISY_LINEAR_SWEEP",
        # )

        # # Square Wave
        # SQUARE_SAMPLE_RATE = 1000

        # self.add_block(
        #     In_Square(
        #         frequency=10,
        #         amplitude=100,
        #         sample_rate=SQUARE_SAMPLE_RATE,
        #         start_time=np.datetime64(time.time_ns(), "ns"),
        #         duty_cycle=0.2,
        #         output_batch_size=SQUARE_SAMPLE_RATE,
        #     ),
        #     output_signal="SQUARE",
        # )

        # self.add_block(
        #     Out_Pyplot_Time_Series_Multiple(
        #         update_rate=1,
        #         samples_to_plot=SQUARE_SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Square Wave (duty=0.2)",
        #         ymin=-200,
        #         ymax=200,
        #     ),
        #     input_signal="SQUARE",
        # )

        # # SIN Wave
        # SINE_SAMPLE_RATE = 1000

        # self.add_block(
        #     In_Sine(
        #         frequency=10,
        #         amplitude=100,
        #         sample_rate=SINE_SAMPLE_RATE,
        #         start_time=np.datetime64(time.time_ns(), "ns"),
        #         output_batch_size=SINE_SAMPLE_RATE,
        #     ),
        #     output_signal="SIN",
        # )

        # self.add_block(
        #     Out_Pyplot_Time_Series_Multiple(
        #         update_rate=1,
        #         samples_to_plot=SINE_SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Sin Wave",
        #         ymin=-200,
        #         ymax=200,
        #     ),
        #     input_signal="SIN",
        # )

        # TRIANGLE_SAMPLE_RATE = 1000

        # self.add_block(
        #     In_Triangle(
        #         frequency=10,
        #         amplitude=100,
        #         sample_rate=TRIANGLE_SAMPLE_RATE,
        #         start_time=np.datetime64(time.time_ns(), "ns"),
        #         output_batch_size=TRIANGLE_SAMPLE_RATE,
        #     ),
        #     output_signal="TRIANGLE",
        # )

        # self.add_block(
        #     Out_Pyplot_Time_Series_Multiple(
        #         update_rate=1,
        #         samples_to_plot=TRIANGLE_SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Triangle Wave",
        #         ymin=-200,
        #         ymax=200,
        #     ),
        #     input_signal="TRIANGLE",
        # )

        # SAWTOOTH_SAMPLE_RATE = 1000

        # self.add_block(
        #     In_Sawtooth(
        #         frequency=10,
        #         amplitude=100,
        #         sample_rate=SAWTOOTH_SAMPLE_RATE,
        #         start_time=np.datetime64(time.time_ns(), "ns"),
        #         output_batch_size=SAWTOOTH_SAMPLE_RATE,
        #     ),
        #     output_signal="SAWTOOTH",
        # )

        # self.add_block(
        #     Out_Pyplot_Time_Series_Multiple(
        #         update_rate=1,
        #         samples_to_plot=SAWTOOTH_SAMPLE_RATE,
        #         figure_num=self.get_next_fig_num(),
        #         title="Sawtooth Wave",
        #         ymin=-200,
        #         ymax=200,
        #     ),
        #     input_signal="SAWTOOTH",
        # )


if __name__ == "__main__":
    f = Fixture_Test_Blocks()
    f.run()
