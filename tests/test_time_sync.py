import pytest
from AcLobsterTopside.time_filter import (
    TickTime,
    WallTime,
    SensorTimestamp,
    LinearFit,
    SimpleTimeMap,
    TimeFilter,
)

# --- TickTime & WallTime Tests ---


def test_tick_time_init():
    t = TickTime(1000, src="GPS", state="PRIMARY")
    assert t.tick_time == 1000
    assert t.src == "GPS"
    assert t.state == "PRIMARY"


# --- SensorTimestamp Tests ---


def test_sensor_timestamp_factories():
    st_tick = SensorTimestamp.from_tick(5000)
    assert "TICK" in st_tick.tick_times
    assert st_tick.get_primary_tick_times()[0] == "TICK"

    st_wall = SensorTimestamp.from_unix_time(100.0, time_ref="SYSTEM")
    # Note: This will fail currently due to the tick_time/wall_time typo in __init__
    assert "SYSTEM" in st_wall.wall_times


def test_sensor_timestamp_add_times():
    st = SensorTimestamp.from_tick(100)
    st.add_tick_time(200, time_ref="AUX", state="DERIVED")
    assert "AUX" in st.tick_times
    assert st.tick_times["AUX"].state == "DERIVED"


# --- LinearFit Tests ---


def test_linear_fit_calculation():
    lf = LinearFit()
    assert not lf.ready()

    # Simple y = 2x + 10
    lf.add_data_point(0, 10)
    lf.add_data_point(10, 30)

    assert lf.ready()
    assert lf.m == 2.0
    assert lf.b == 10.0
    assert lf.interpolate(5) == 20.0


def test_linear_fit_duplicate_points():
    lf = LinearFit()
    lf.add_data_point(1, 1)
    lf.add_data_point(1, 1)  # Should ignore to avoid division by zero
    assert not lf.ready()


# --- SimpleTimeMap Tests ---


def test_simple_time_map_bidirectional():
    tm = SimpleTimeMap(["A", "B"])
    tm.add_time_ref("A", 10, "B", 100)
    tm.add_time_ref("A", 20, "B", 200)

    assert tm.map_time("A", 15, "B") == 150
    assert tm.map_time("B", 150, "A") == 15


# --- TimeFilter Tests ---


def test_time_filter_init():
    tf = TimeFilter(output_tick_times=("TICK",), output_wall_times=("COMP",))
    assert tf.output_tick_times == ("TICK",)
    assert isinstance(tf.time_map, SimpleTimeMap)


def test_time_filter_processing():
    tf = TimeFilter(output_tick_times=("TICK",), output_wall_times=("COMP",))

    # Create a timestamp with two primary sources to establish a relationship
    st = SensorTimestamp(
        tick_time=TickTime(100, src="TICK", state="PRIMARY"),
        wall_time=WallTime(1000.0, src="COMP", state="PRIMARY"),
    )

    tf.process_timestamp(st)

    # Create a second point to allow LinearFit to calculate slope
    st2 = SensorTimestamp(
        tick_time=TickTime(200, src="TICK", state="PRIMARY"),
        wall_time=WallTime(1100.0, src="COMP", state="PRIMARY"),
    )
    tf.process_timestamp(st2)

    # Now provide a timestamp with only TICK, see if it derives COMP
    st3 = SensorTimestamp.from_tick(250)
    tf.process_timestamp(st3)

    assert "COMP" in st3.wall_times
    assert st3.wall_times["COMP"].wall_time == 1150.0


def test_out_of_order_packets():
    tf = TimeFilter(output_wall_times=("COMP",))
    # T=100
    tf.process_timestamp(
        SensorTimestamp(
            TickTime(100, "TICK", "PRIMARY"), WallTime(1000, "COMP", "PRIMARY")
        )
    )
    # T=200
    tf.process_timestamp(
        SensorTimestamp(
            TickTime(200, "TICK", "PRIMARY"), WallTime(2000, "COMP", "PRIMARY")
        )
    )
    # Delayed T=150 arrives!
    tf.process_timestamp(
        SensorTimestamp(
            TickTime(150, "TICK", "PRIMARY"), WallTime(1500, "COMP", "PRIMARY")
        )
    )

    # After 150 arrives, the 'last_x' is 150.
    # If we now try to map 250, will it use the slope between 200 and 150?
    st = SensorTimestamp.from_tick(250)
    tf.process_timestamp(st)
    assert st.get_wall_time("COMP") == 2500.0


def test_zero_delta_protection():
    lf = LinearFit()
    lf.add_data_point(100, 1000)
    # Simulate a duplicate packet or a stuck clock
    lf.add_data_point(100, 1000)

    assert lf.m is None
    assert not lf.ready()


def test_linear_fit_updates():
    lf = LinearFit()
    # First slope: 1.0
    lf.add_data_point(0, 0)
    lf.add_data_point(10, 10)
    assert lf.m == 1.0

    # Second slope: 2.0 (based on points (10,10) and (20,30))
    lf.add_data_point(20, 30)
    assert lf.m == 2.0
    assert lf.interpolate(25) == 40.0  # 2.0 * 25 + (-10)


def test_filter_insufficient_data():
    tf = TimeFilter(output_wall_times=("COMP",))
    # Only one point—mapping exists but is not "ready"
    st1 = SensorTimestamp(
        tick_time=TickTime(100, src="TICK", state="PRIMARY"),
        wall_time=WallTime(1000.0, src="COMP", state="PRIMARY"),
    )
    tf.process_timestamp(st1)

    st2 = SensorTimestamp.from_tick(200)
    tf.process_timestamp(st2)

    # Should not have derived COMP because m and b are still None
    assert "COMP" not in st2.wall_times


def test_numeric_type_mixing():
    st = SensorTimestamp(
        tick_time=TickTime(100, src="TICK"),
        wall_time=WallTime(1600000000.5, src="COMP"),
    )
    # Ensure getters return expected types
    assert isinstance(st.get_tick_time("TICK"), (int, float))
    assert isinstance(st.get_wall_time("COMP"), float)
