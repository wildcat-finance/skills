"""Capture stops before exceeding its declared runtime envelope."""

import unittest

from lazarus_lib.errors import ResourceLimitError
from lazarus_lib.limits import CaptureLimits


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class LimitTests(unittest.TestCase):
    def values(self, **changes):
        values = {
            "max_requests": 2,
            "max_component_bytes": 10,
            "max_total_bytes": 15,
            "max_elapsed_seconds": 5,
        }
        values.update(changes)
        return values

    def test_request_and_response_byte_limits_fail_closed(self):
        limits = CaptureLimits(self.values())
        limits.before_request(2)
        with self.assertRaisesRegex(ResourceLimitError, "RPC requests"):
            limits.before_request()
        limits.after_response(8)
        self.assertEqual(limits.response_read_limit(), 7)
        with self.assertRaisesRegex(ResourceLimitError, "response bytes"):
            limits.after_response(8)

    def test_component_limit_is_checked_before_total(self):
        limits = CaptureLimits(self.values(max_total_bytes=100))
        with self.assertRaisesRegex(ResourceLimitError, "RPC response"):
            limits.after_response(11)

    def test_elapsed_time_is_checked_before_and_after_io(self):
        clock = Clock()
        limits = CaptureLimits(self.values(), clock=clock)
        clock.value = 4.9
        limits.before_request()
        clock.value = 5.0
        with self.assertRaisesRegex(ResourceLimitError, "seconds"):
            limits.after_response(1)

    def test_one_budget_is_shared_across_provider_clients(self):
        limits = CaptureLimits(self.values(max_requests=4, max_total_bytes=20))
        primary = limits
        anchor = limits
        primary.before_request(2)
        primary.after_response(8)
        anchor.before_request(2)
        anchor.after_response(7)
        with self.assertRaisesRegex(ResourceLimitError, "RPC requests"):
            primary.before_request()
        with self.assertRaisesRegex(ResourceLimitError, "response bytes"):
            anchor.after_response(6)


if __name__ == "__main__":
    unittest.main()
