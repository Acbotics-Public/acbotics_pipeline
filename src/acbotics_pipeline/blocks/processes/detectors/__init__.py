# import acbotics_pipeline.blocks.processes.detectors.pr_detect_bf_peak_1d # resolve dependencies
import acbotics_pipeline.blocks.processes.detectors.pr_energy_detector
import acbotics_pipeline.blocks.processes.detectors.pr_relative_energy_detector
import acbotics_pipeline.blocks.processes.detectors.pr_windowed_detector


from acbotics_pipeline.blocks.processes.detectors.pr_energy_detector import (
    Pr_Energy_Detector,
)

try:
    import acbotics_pipeline.blocks.processes.detectors.pr_frequency_detector

    from acbotics_pipeline.blocks.processes.detectors.pr_frequency_detector import (
        Pr_Frequency_Detector,
    )
except ModuleNotFoundError:
    print("arlpy not installed. skipping Pr_Frequency_Detector")
from acbotics_pipeline.blocks.processes.detectors.pr_relative_energy_detector import (
    Pr_Relative_Energy_Detector,
)
from acbotics_pipeline.blocks.processes.detectors.pr_windowed_detector import (
    Pr_Windowed_Detector,
)
