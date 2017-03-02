from unittest import TestCase, main

import numpy as np
import numpy.testing as npt

from trouver.events import Events
from trouver.transformations import (_debounce, _filter_durations,
                                     _offset_events, merge_overlap)
from trouver.transformations import debounce, filter_durations, offset_events


class TransformationTestFixture(TestCase):
    def setUp(self):
        raise NotImplementedError

    def fixture(self, control_starts, control_stops, period, **kwargs):
        input_events = Events(self.starts, self.stops, period, 'input', self.condition.size)

        test_events = self.transformation(input_events, **kwargs)
        test_starts, test_stops = test_events._starts, test_events._stops

        npt.assert_array_equal(control_starts, test_starts)
        npt.assert_array_equal(control_stops, test_stops)


class TestDebounce(TransformationTestFixture):
    def setUp(self):
        self.condition = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1])
        self.starts = np.array([2, 7, 11])
        self.stops = np.array([4, 10, 12])
        self.transformation = _debounce

    def test_entry_debounce(self):
        period = 1
        control_starts = np.array([2, 7])
        control_stops = np.array([4, 10])
        self.fixture(control_starts, control_stops, period, entry_debounce=2, exit_debounce=0)

    def test_exit_debounce(self):
        period = 1
        control_starts = np.array([2, 7])
        control_stops = np.array([4, 12])
        self.fixture(control_starts, control_stops, period, entry_debounce=0, exit_debounce=2)

    def test_entry_and_exit_debounce(self):
        period = 1
        control_starts = np.array([2])
        control_stops = np.array([12])
        self.fixture(control_starts, control_stops, period, entry_debounce=2, exit_debounce=3.1)

    def test_non_int_debounces(self):
        period = 1
        control_starts = np.array([2, 7, 11])
        control_stops = np.array([4, 10, 12])
        self.fixture(control_starts, control_stops, period,
                     entry_debounce=float(0.00000001),
                     exit_debounce=float(0.99999999))

    def test_period_100ms(self):
        period = 0.1
        control_starts = np.array([2, 7])
        control_stops = np.array([4, 12])
        self.fixture(control_starts, control_stops, period, entry_debounce=0.15, exit_debounce=0.2)

    def test_period_120ms(self):
        period = 0.12
        control_starts = np.array([2, 7])
        control_stops = np.array([4, 12])
        self.fixture(control_starts, control_stops, period, entry_debounce=0.15, exit_debounce=0.2)


class TestDurationFilter(TransformationTestFixture):
    def setUp(self):
        self.condition = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1])
        self.starts = np.array([2, 7, 11])
        self.stops = np.array([4, 10, 12])
        self.transformation = _filter_durations

    def test_mindur(self):
        period = 1
        control_starts = np.array([2, 7])
        control_stops = np.array([4, 10])
        self.fixture(control_starts, control_stops, period, mindur=2, maxdur=None)

    def test_maxdur(self):
        period = 1
        control_starts = np.array([2, 11])
        control_stops = np.array([4, 12])
        self.fixture(control_starts, control_stops, period, mindur=0, maxdur=2)

    def test_mindur_maxdur(self):
        period = 1
        control_starts = np.array([2, 7])
        control_stops = np.array([4, 10])
        self.fixture(control_starts, control_stops, period, mindur=2, maxdur=3.1)

    def test_nonint_durs(self):
        period = 1
        control_starts = np.array([2])
        control_stops = np.array([4])
        self.fixture(control_starts, control_stops, period,
                     mindur=float(1.00000001),
                     maxdur=float(2.99999999))

    def test_period_100ms(self):
        period = 0.1
        control_starts = np.array([2])
        control_stops = np.array([4])
        self.fixture(control_starts, control_stops, period, mindur=0.15, maxdur=0.2)

    def test_period_120ms(self):
        period = 0.12
        control_starts = np.array([2])
        control_stops = np.array([4])
        self.fixture(control_starts, control_stops, period, mindur=0.15, maxdur=0.35)


class TestOffsets(TransformationTestFixture):
    def setUp(self):
        self.condition = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1])
        self.starts = np.array([2, 7, 11])
        self.stops = np.array([4, 10, 12])
        self.transformation = _offset_events

    def test_start_offset(self):
        period = 1
        control_starts = np.array([1, 6, 10])
        control_stops = np.array([4, 10, 12])
        self.fixture(control_starts, control_stops, period, start_offset=-1, stop_offset=0)

    def test_stop_offset(self):
        period = 1
        control_starts = np.array([2, 7, 11])
        control_stops = np.array([5, 11, 12])
        self.fixture(control_starts, control_stops, period, start_offset=0, stop_offset=1)

    def test_start_stop_offset(self):
        period = 1
        control_starts = np.array([1, 6, 10])
        control_stops = np.array([5, 11, 12])
        self.fixture(control_starts, control_stops, period, start_offset=-1, stop_offset=1)

    def test_period_100ms_start_stop_offset(self):
        period = 0.1
        control_starts = np.array([1, 6, 10])
        control_stops = np.array([5, 11, 12])
        self.fixture(control_starts, control_stops, period, start_offset=-0.1, stop_offset=0.1)

    def test_period_120ms_start_stop_offset(self):
        period = 0.12
        control_starts = np.array([1, 6, 10])
        control_stops = np.array([5, 11, 12])
        self.fixture(control_starts, control_stops, period, start_offset=-0.1, stop_offset=0.1)


class TestMergeOverlap(TransformationTestFixture):
    def setUp(self):
        self.condition = np.ones(15)
        self.starts = np.array([1, 3, 13])
        self.stops = np.array([5, 7, 15])
        self.transformation = merge_overlap

    def test_merge_overlap(self):
        period = 1
        control_starts = np.array([1, 13])
        control_stops = np.array([7, 15])
        self.fixture(control_starts, control_stops, period)

    def test_events_where_edges_touch(self):
        period = 1
        self.starts = np.array([1, 7])
        self.stops = np.array([7, 15])
        control_starts = np.array([1])
        control_stops = np.array([15])
        self.fixture(control_starts, control_stops, period)


class TestNoEvents(TransformationTestFixture):
    def setUp(self):
        self.condition = np.ones(10)
        self.starts = np.array([])
        self.stops = np.array([])

    def test_debounce_no_events(self):
        self.transformation = _debounce
        period = 1
        control_starts = np.array([])
        control_stops = np.array([])
        self.fixture(control_starts, control_stops, period, entry_debounce=2, exit_debounce=3.1)

    def test_duration_filter_no_events(self):
        self.transformation = _filter_durations
        period = 1
        control_starts = np.array([])
        control_stops = np.array([])
        self.fixture(control_starts, control_stops, period, mindur=2, maxdur=3.1)

    def test_offsets_no_events(self):
        self.transformation = _offset_events
        period = 1
        control_starts = np.array([])
        control_stops = np.array([])
        self.fixture(control_starts, control_stops, period, start_offset=-2, stop_offset=3.1)


class TestDefaultArguments(TransformationTestFixture):
    """Test default arguments of all functions

    The input of these functions should match the output exactly.
    Default arguments are expected to be no-ops.
    """
    def setUp(self):
        self.condition = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1])
        self.period = 1
        self.starts = np.array([2, 7, 11])
        self.stops = np.array([4, 10, 12])

    def test_debounce_defaults(self):
        self.transformation = debounce()
        control_starts = self.starts
        control_stops = self.stops
        self.fixture(control_starts, control_stops, self.period)

    def test_duration_filter_defaults(self):
        self.transformation = filter_durations()
        control_starts = self.starts
        control_stops = self.stops
        self.fixture(control_starts, control_stops, self.period)

    def test_offset_defaults(self):
        self.transformation = offset_events()
        control_starts = self.starts
        control_stops = self.stops
        self.fixture(control_starts, control_stops, self.period)


if __name__ == '__main__':
    main()
