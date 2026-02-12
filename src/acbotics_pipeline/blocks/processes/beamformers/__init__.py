# import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_3d # resolve dependencies
import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_bartlett

# import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_both #resolve dependencies
# import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_raw
import acbotics_pipeline.blocks.processes.beamformers.pr_directional_beamformer

# import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_3d # resolve dependencies
try:
    from acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_bartlett import (
        Pr_Beamformer_Bartlett,
    )
except ModuleNotFoundError:
    print("arlpy not found. Skipping.")

# import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_both #resolve dependencies
# import acbotics_pipeline.blocks.processes.beamformers.pr_beamformer_raw
from acbotics_pipeline.blocks.processes.beamformers.pr_directional_beamformer import (
    Pr_Directional_Beamformer,
)
