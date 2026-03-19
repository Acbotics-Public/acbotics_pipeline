from acbotics_pipeline.utils.timing.time_filter import SensorTimestamp


class Generic_Sensor_To_Data_Container:
    def __init__(self, time_filter=None):
        self.time_filter = time_filter

    def _get_sensor_timestamp(self, header):
        sensor_time = SensorTimestamp.from_tick(
            tick_time_int=header.start_time_nsec
        )  # TODO: Use Time ref?
        if self.time_filter is not None:
            self.time_filter.process_timestamp(sensor_time)
        return sensor_time
