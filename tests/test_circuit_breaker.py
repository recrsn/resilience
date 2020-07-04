import datetime
from time import sleep
from unittest.mock import MagicMock

import pytest

from resilience.exceptions import CallNotAllowedException
from resilience.circuit_breaker import CircuitBreaker, OPEN, HALF_OPEN, CLOSED


def test_circuit_breaker_calls_function_when_not_open():
    mock_fn = MagicMock()

    cb = CircuitBreaker(name="test")
    decorated = cb(mock_fn)

    decorated("value")

    mock_fn.assert_called_with("value")


def test_circuit_breaker_reraises_exceptions_on_failure():
    def failing_func():
        raise Exception("always fails")

    cb = CircuitBreaker(name="test")
    decorated = cb(failing_func)

    with pytest.raises(Exception) as ex:
        decorated()

    assert "always fails" == str(ex.value)


def test_circuit_breaker_transitions_to_open_state_after_errors_cross_threshold():
    def failing_func():
        raise Exception("always fails")

    cb = CircuitBreaker(name="test")
    decorated = cb(failing_func)

    for _ in range(6):
        try:
            decorated()
        except:
            pass

    assert cb.state == OPEN


def test_circuit_breaker_transitions_does_not_transition_to_open_state_on_ignored_exception():
    def failing_func():
        raise AssertionError()

    cb = CircuitBreaker(name="test", allowed_exceptions=[AssertionError])
    decorated = cb(failing_func)

    for _ in range(10):
        try:
            decorated()
        except:
            pass

    assert cb.state == CLOSED


def test_calls_on_open_circuit_breaker_raises_call_not_permitted_exception():
    def failing_func():
        raise Exception("always fails")

    cb = CircuitBreaker(name="test")
    decorated = cb(failing_func)

    for _ in range(6):
        try:
            decorated()
        except:
            pass

    with pytest.raises(CallNotAllowedException) as ex:
        decorated()

    assert "Circuit breaker is open" == str(ex.value)


def test_circuit_breaker_transitions_to_half_open_after_trip_duration():
    def failing_func():
        raise Exception("always fails")

    cb = CircuitBreaker(name="test", trip_duration=datetime.timedelta(seconds=1))
    decorated = cb(failing_func)

    for _ in range(10):
        try:
            decorated()
        except:
            pass

    assert cb.state == OPEN

    sleep(1)

    assert cb.state == HALF_OPEN


def test_circuit_breaker_transitions_to_open_on_failure_after_half_open():
    def failing_func():
        raise Exception("always fails")

    cb = CircuitBreaker(name="test", trip_duration=datetime.timedelta(seconds=1))
    decorated = cb(failing_func)

    for _ in range(10):
        try:
            decorated()
        except:
            pass

    assert cb.state == OPEN

    sleep(1)

    assert cb.state == HALF_OPEN

    try:
        decorated()
    except:
        pass

    assert cb.state == OPEN


def test_circuit_breaker_transitions_to_closed_on_no_failures_in_half_open():
    def func(val):
        if val:
            raise Exception()

    cb = CircuitBreaker(name="test", trip_duration=datetime.timedelta(seconds=1), allowed_calls_in_half_open=2)
    decorated = cb(func)

    for i in range(6):
        try:
            decorated(True)
        except:
            pass

    assert cb.state == OPEN

    sleep(1)

    assert cb.state == HALF_OPEN

    decorated(False)

    assert cb.state == HALF_OPEN

    decorated(False)
    decorated(False)

    assert cb.state == CLOSED


def test_circuit_breaker_reset_resets_the_circuit_breaker():
    def func(val):
        if val:
            raise Exception()

    cb = CircuitBreaker(name="test", trip_duration=datetime.timedelta(seconds=1), allowed_calls_in_half_open=2)
    decorated = cb(func)

    for i in range(6):
        try:
            decorated(True)
        except:
            pass

    assert cb.state == OPEN

    cb.reset()

    assert cb.state == CLOSED
