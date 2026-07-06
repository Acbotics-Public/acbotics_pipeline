import acbotics_pipeline.helpers.contract_helpers as ch
import numpy as np


class TickTime:
    VALID_STATES = ("INVALID", "PRIMARY", "DERIVED")

    @ch.argtype("state", (str))
    @ch.argtype("src", (str))
    @ch.argtype("tick_time", (int, float, np.int64))
    @ch.argin("state", VALID_STATES)
    def __init__(self, tick_time, src="TICK", state="PRIMARY", tick_step=1e-9):
        """Create a tick time. src is used if there are multiple tick time bases in
        the system that need to be disambiguated"""
        self.tick_time = float(tick_time)
        self.src = src
        self.state = state
        self.tick_step = tick_step

    def __repr__(self):
        return "Tick Time: SRC=%s, state=%s" % (self.src, self.state)


class WallTime:
    VALID_STATES = ("INVALID", "PRIMARY", "DERIVED")

    @ch.argtype("wall_time", (int, float))
    @ch.argtype("state", (str))
    @ch.argtype("src", (str))
    @ch.argin("state", VALID_STATES)
    @ch.arg_nonnegative("wall_time")
    @ch.argin("state", VALID_STATES)
    def __init__(self, wall_time, src="COMP", state="PRIMARY"):
        """Create a tick time. src is used if there are multiple tick time bases in
        the system that need to be disambiguated"""
        self.wall_time = wall_time
        self.src = src
        self.state = state

    def __repr__(self):
        return "Wall Time: SRC=%s, state=%s, time=%f" % (
            self.src,
            self.state,
            self.wall_time,
        )


class SensorTimestamp:
    @ch.argtype("tick_time", (TickTime, None))
    @ch.argtype("wall_time", (WallTime, None))
    # @ch.arg_at_least_one_not_none("tick_time", "wall_time")
    def __init__(self, tick_time=None, wall_time=None):
        self.tick_times = {}
        self.wall_times = {}
        if tick_time is not None:
            self.tick_times[tick_time.src] = tick_time
        if wall_time is not None:
            self.wall_times[wall_time.src] = wall_time

    @classmethod
    # @ch.argtype("tick_time_int", int)
    def from_tick(
        cls,
        tick_time_int,
    ):
        return cls(
            tick_time=TickTime(tick_time=tick_time_int, src="TICK", state="PRIMARY")
        )

    @classmethod
    # @ch.argtype("unix_time_float", (int, float))
    # @ch.argtype("time_ref", str)
    def from_unix_time(cls, unix_time_float, time_ref="COMP"):
        return cls(
            wall_time=WallTime(wall_time=unix_time_float, src=time_ref, state="PRIMARY")
        )

    @ch.argtype("tick_time_int", (int, float))
    @ch.argtype("time_ref", str)
    def add_tick_time(self, tick_time_int, time_ref="TICK", state="DERIVED"):
        self.tick_times[time_ref] = TickTime(
            tick_time=tick_time_int, src=time_ref, state=state
        )

    @ch.argtype("unix_time_float", (int, float))
    @ch.argtype("time_ref", str)
    def add_wall_time(self, unix_time_float, time_ref="COMP", state="DERIVED"):
        if unix_time_float <= 0:
            print(f"Refusing to use negative wall time {unix_time_float}")
            return
        self.wall_times[time_ref] = WallTime(
            wall_time=unix_time_float, src=time_ref, state=state
        )

    @ch.result_type((int, float))
    @ch.argtype("time_ref", str)
    def get_tick_time(self, time_ref="TICK"):
        return self.tick_times[time_ref].tick_time

    @ch.argtype("time_ref", str)
    @ch.result_type((float, int))
    def get_wall_time(self, time_ref="COMP"):
        return self.wall_times[time_ref].wall_time

    @ch.result_type(tuple)
    def get_primary_tick_times(self):
        primaries = []
        for k, v in self.tick_times.items():
            if v.state == "PRIMARY":
                primaries.append(k)
        return tuple(primaries)

    @ch.result_type(tuple)
    def get_all_tick_times(self):
        return tuple(self.tick_times.keys())

    @ch.result_type(tuple)
    def get_all_wall_times(self):
        return tuple(self.wall_times.keys())

    def get_primary_wall_times(self):
        primaries = []
        for k, v in self.wall_times.items():
            if v.state == "PRIMARY":
                primaries.append(k)
        return primaries

    def __repr__(self):
        return (
            "SensorTimestamp: \r\n  Tick Times: "
            + repr(self.tick_times)
            + "\r\n  Wall Times: "
            + repr(self.wall_times)
        )


class LinearFit:
    def __init__(self):
        self.m = None
        self.b = None
        self.last_x = None
        self.last_y = None
        self.skip = 0

    def add_data_point(self, x, y):
        if self.last_x is not None and self.last_y is not None:
            if self.last_x == x or self.last_y == y:
                return  # can't make cal if no changes is one variable
            if self.skip < 1000:
                self.skip += 1
                return
            self.skip = 0
            dx = x - self.last_x
            dy = y - self.last_y
            self.m = dy / dx
            self.b = y - self.m * x

        self.last_x = x
        self.last_y = y

    def __repr__(self):
        if self.ready():
            return "Linear fit, m=%f, b=%f" % (self.m, self.b)
        else:
            return "Linear fit, not ready"

    def interpolate(self, x):
        return self.m * x + self.b

    # def interpolate(self, x):
    #     print("Interpolating " + repr(x))
    #     res = (x - self.b) / self.m
    #     print("Result" + repr(res))
    #     print(self)
    #     return res

    def ready(self):
        return self.m is not None and self.b is not None


class SimpleTimeMap:
    def __init__(self, time_names=("GPS", "COMP", "TICK")):
        print(f"--- INITIALIZING NEW MAP: {id(self)} ---")
        self.time_names = tuple(time_names)
        self.time_map = {}
        for t1 in self.time_names:
            for t2 in self.time_names:
                if not t1 == t2:
                    self.time_map[(t1, t2)] = LinearFit()

    def add_time_ref(self, name1, time1, name2, time2):
        self.time_map[(name1, name2)].add_data_point(time1, time2)
        self.time_map[(name2, name1)].add_data_point(time2, time1)
        self.time_map["DEBUG"] = "DEADBEEF"

    def map_time(self, src_name, src_val, tgt_name):
        try:
            lf = self.time_map[(src_name, tgt_name)]
            if lf.ready():
                # print("Mapped from %s to %s" % (src_name, tgt_name))
                return lf.interpolate(src_val)
        except KeyError:
            print("Key Error")

            return None
        # print("Failed. Not Ready?")
        return None


class TimeFilter:
    def __init__(self, output_tick_times=("TICK",), output_wall_times=("COMP",)):
        self.output_tick_times = tuple(output_tick_times)
        self.output_wall_times = tuple(output_wall_times)
        self.tick_times = {}
        self.wall_timkes = {}
        self.time_map = SimpleTimeMap()

    def _extract_timestamp(self, timestamp):
        ptts = timestamp.get_primary_tick_times()
        pwts = timestamp.get_primary_wall_times()
        if len(ptts) + len(pwts) > 1:
            # print("Extracting time from timestamp")
            # print(timestamp)
            # Multiple primary times. Let's add a mapping
            for src_ptt in ptts:
                # find any tick to tick mappings
                for tgt_ptt in ptts:
                    if src_ptt == tgt_ptt:
                        continue
                    time1 = timestamp.get_tick_time(time_ref=src_ptt)
                    time2 = timestamp.get_tick_time(time_ref=tgt_ptt)
                    self.time_map.add_time_ref(
                        name1=src_ptt, time1=time1, name2=tgt_ptt, time2=time2
                    )
                # find any tick to wall mappings
                for tgt_pwt in pwts:
                    # don't need to check for duplicate as one is tick and the other is wall
                    time1 = timestamp.get_tick_time(time_ref=src_ptt)
                    time2 = timestamp.get_wall_time(time_ref=tgt_pwt)
                    self.time_map.add_time_ref(
                        name1=src_ptt, time1=time1, name2=tgt_pwt, time2=time2
                    )
            for src_pwt in pwts:
                # find any time to time mappings
                for tgt_pwt in pwts:
                    if src_pwt == tgt_pwt:
                        continue
                    time1 = timestamp.get_wall_time(time_ref=src_pwt)
                    time2 = timestamp.get_wall_time(time_ref=tgt_pwt)
                    self.time_map.add_time_ref(
                        name1=src_pwt, time1=time1, name2=tgt_pwt, time2=time2
                    )

    def _fill_in_output_ticks(self, timestamp):
        ptts = timestamp.get_primary_tick_times()
        pwts = timestamp.get_primary_wall_times()

        for ott in self.output_tick_times:
            if ott in ptts:
                continue  # it's a primary
            estimated_tick_times = []
            for ptt in ptts:
                src_time = timestamp.get_tick_time(time_ref=ptt)
                est = self.time_map.map_time(
                    src_name=ptt, src_val=src_time, tgt_name=ott
                )
                if est is not None:
                    estimated_tick_times.append(est)
            for pwt in pwts:

                src_time = timestamp.get_wall_time(time_ref=pwt)
                est = self.time_map.map_time(
                    src_name=pwt, src_val=src_time, tgt_name=ott
                )
                if est is not None:
                    estimated_tick_times.append(est)
                else:
                    print("No estimate for time between %s and %s" % (pwt, ott))
            found_times = len(estimated_tick_times)
            if found_times == 0:
                continue  # TODO: Should we but a placeholder?
            elif found_times == 1:
                timestamp.add_tick_time(
                    estimated_tick_times[0], time_ref=ott, state="DERIVED"
                )
            else:
                average_acc = 0
                for v in estimated_tick_times:
                    average_acc += v
                average = average_acc / found_times
                timestamp.add_tick_time(average, time_ref=ott, state="DERIVED")

    def _fill_in_output_wall(self, timestamp):
        ptts = timestamp.get_primary_tick_times()
        pwts = timestamp.get_primary_wall_times()
        for owt in self.output_wall_times:
            if owt in pwts:
                continue  # it's a primary
            estimated_wall_times = []
            for ptt in ptts:
                src_time = timestamp.get_tick_time(time_ref=ptt)
                est = self.time_map.map_time(
                    src_name=ptt, src_val=src_time, tgt_name=owt
                )
                if est is not None:
                    estimated_wall_times.append(est)
            for pwt in pwts:
                src_time = timestamp.get_wall_time(time_ref=pwt)
                est = self.time_map.map_time(
                    src_name=pwt, src_val=src_time, tgt_name=owt
                )
                if est is not None:
                    estimated_wall_times.append(est)
            found_times = len(estimated_wall_times)
            if found_times == 0:
                continue  # TODO: Should we but a placeholder?
            elif found_times == 1:
                timestamp.add_wall_time(
                    estimated_wall_times[0], time_ref=owt, state="DERIVED"
                )
            else:
                average_acc = 0
                for v in estimated_wall_times:
                    average_acc += v
                average = average_acc / found_times
                timestamp.add_wall_time(average, time_ref=owt, state="DERIVED")

    def process_timestamp(self, timestamp):
        """Takes in a timestamp, extracts primary information from sensors with multiple primary sources.
        Fills in any fields that can be calculated with existing data."""

        self._extract_timestamp(timestamp)
        self._fill_in_output_ticks(timestamp)
        self._fill_in_output_wall(timestamp)
        # now let's fill in any missing tick times:
        # now let's fill in any missing wall times:
