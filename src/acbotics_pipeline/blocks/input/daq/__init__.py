try:
    import acbotics_pipeline.blocks.input.daq.in_mcc_daq_events
    import acbotics_pipeline.blocks.input.daq.in_mcc_daq_events_raw
    import acbotics_pipeline.blocks.input.daq.in_mcc_daq_events_raw_multiple
    import acbotics_pipeline.blocks.input.daq.in_mcc_daq_events_raw_process

    from acbotics_pipeline.blocks.input.daq.in_mcc_daq_events import In_Mcc_DAQ_Event
    from acbotics_pipeline.blocks.input.daq.in_mcc_daq_events_raw import (
        In_Mcc_DAQ_Event_Raw,
    )
    from acbotics_pipeline.blocks.input.daq.in_mcc_daq_events_raw_multiple import (
        In_Mcc_DAQ_Event_Raw_Multiple,
    )
    from acbotics_pipeline.blocks.input.daq.in_mcc_daq_events_raw_process import (
        In_Mcc_DAQ_Event_Raw_Process,
    )


except ModuleNotFoundError:
    print("MCC Modules not installed. Skipping MCC Blocks.")
