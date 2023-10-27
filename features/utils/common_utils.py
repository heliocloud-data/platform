"""
Contains common utilities for feature tests.
"""
import time

# pylint: disable=keyword-arg-before-vararg


def wait_until(somepredicate, timeout, period=0.25, *args, **kwargs):
    """
    Wait until the predicate returns true OR the timeout.
    """
    mustend = time.time() + timeout
    while time.time() < mustend:
        if somepredicate(*args, **kwargs):
            return True
        time.sleep(period)
    return False
