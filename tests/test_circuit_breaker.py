import datetime
from time import sleep
from unittest.mock import MagicMock

import pytest

from resilience.circuit_breaker import CircuitBreaker, OPEN, HALF_OPEN, CLOSED
from resilience.exceptions import CallNotAllowedException


# pylint: disable=bare-except
# noinspection PyBroadException

def test_circuit_breaker_calls_function_when_not_open():
    mock_fn = MagicMock()

    circuit_breaker = CircuitBreaker(name="test")
    decorated = circuit_breaker(mock_fn)

    decorated("value")

    mock_fn.assert_called_with("value")


def test_circuit_breaker_reraises_exceptions_on_failure():
    def failing_func():
        raise Exception("always fails")

    circuit_breaker = CircuitBreaker(name="test")
    decorated = circuit_breaker(failing_func)

    with pytest.raises(Exception) as ex:
        decorated()

    assert str(ex.value) == "always fails"


def test_circuit_breaker_transitions_to_open_state_after_errors_cross_threshold():
    def failing_func():
        raise Exception("always fails")

    circuit_breaker = CircuitBreaker(name="test")
    decorated = circuit_breaker(failing_func)

    for _ in range(6):
        try:
            decorated()
        except:
            pass

    assert circuit_breaker.state == OPEN


def test_circuit_breaker_transitions_does_not_transition_to_open_state_on_ignored_exception():
    def failing_func():
        raise AssertionError()

    circuit_breaker = CircuitBreaker(
        name="test", allowed_exceptions=[AssertionError])
    decorated = circuit_breaker(failing_func)

    for _ in range(10):
        try:
            decorated()
        except:
            pass

    assert circuit_breaker.state == CLOSED


def test_calls_on_open_circuit_breaker_raises_call_not_permitted_exception():
    def failing_func():
        raise Exception("always fails")

    circuit_breaker = CircuitBreaker(name="test")
    decorated = circuit_breaker(failing_func)

    for _ in range(6):
        try:
            decorated()
        except:
            pass

    with pytest.raises(CallNotAllowedException) as ex:
        decorated()

    assert str(ex.value) == "Circuit breaker is open"


def test_circuit_breaker_transitions_to_half_open_after_trip_duration():
    def failing_func():
        raise Exception("always fails")

    circuit_breaker = CircuitBreaker(
        name="test", trip_duration=datetime.timedelta(seconds=1))
    decorated = circuit_breaker(failing_func)

    for _ in range(10):
        try:
            decorated()
        except:
            pass

    assert circuit_breaker.state == OPEN

    sleep(1)

    assert circuit_breaker.state == HALF_OPEN


def test_circuit_breaker_transitions_to_open_on_failure_after_half_open():
    def failing_func():
        raise Exception("always fails")

    circuit_breaker = CircuitBreaker(
        name="test", trip_duration=datetime.timedelta(seconds=1))
    decorated = circuit_breaker(failing_func)

    for _ in range(10):
        try:
            decorated()
        except:
            pass

    assert circuit_breaker.state == OPEN

    sleep(1)

    assert circuit_breaker.state == HALF_OPEN

    try:
        decorated()
    except:
        pass

    assert circuit_breaker.state == OPEN


def test_circuit_breaker_transitions_to_closed_on_no_failures_in_half_open():
    def func(val):
        if val:
            raise Exception()

    circuit_breaker = CircuitBreaker(name="test", trip_duration=datetime.timedelta(
        seconds=1), allowed_calls_in_half_open=2)
    decorated = circuit_breaker(func)

    for _ in range(6):
        try:
            decorated(True)
        except:
            pass

    assert circuit_breaker.state == OPEN

    sleep(1)

    assert circuit_breaker.state == HALF_OPEN

    decorated(False)

    assert circuit_breaker.state == HALF_OPEN

    decorated(False)
    decorated(False)

    assert circuit_breaker.state == CLOSED


def test_setting_circuit_breaker_to_closed_resets_state():
    def func(val):
        if val:
            raise Exception()

    circuit_breaker = CircuitBreaker(name="test",
                                     trip_duration=datetime.timedelta(
                                         seconds=1),
                                     allowed_calls_in_half_open=2)
    decorated = circuit_breaker(func)

    for _ in range(6):
        try:
            decorated(True)
        except:
            pass

    assert circuit_breaker.state == OPEN

    circuit_breaker.state = CLOSED

    try:
        decorated(True)
    except:
        pass

    assert circuit_breaker.state == CLOSED
