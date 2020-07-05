from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from resilience.retry import Retry, EXPONENTIAL


def test_retry_should_call_original_function():
    def func():
        return "value"

    retry = Retry(retriable_exceptions=[ValueError])
    decorated = retry(func)

    return_value = decorated()

    assert return_value == "value"


def test_retry_should_not_retry_for_exception_not_in_retry_list():
    def failing_func():
        raise AssertionError("error")

    retry = Retry(retriable_exceptions=[ValueError])
    decorated = retry(failing_func)

    with pytest.raises(AssertionError) as exception:
        decorated()

    assert str(exception.value) == "error"


def test_retry_should_retry_for_specified_times_and_return_error_if_all_retries_failed():
    mock_method = MagicMock()
    mock_method.side_effect = ValueError("error")

    retry = Retry(retriable_exceptions=[ValueError])
    decorated = retry(mock_method)

    with pytest.raises(ValueError) as exception:
        decorated()

    assert str(exception.value) == "error"
    assert mock_method.call_count == 3


def test_retry_should_retry_with_linear_delay():
    invoked = []

    def failing_func():
        invoked.append(datetime.now())
        raise ValueError("error")

    interval = timedelta(milliseconds=10)
    retry = Retry(retriable_exceptions=[ValueError], interval=interval)
    decorated = retry(failing_func)

    with pytest.raises(ValueError) as exception:
        decorated()

    assert str(exception.value) == "error"

    assert invoked[1] - invoked[0] >= interval
    assert invoked[2] - invoked[1] >= interval


def test_retry_should_retry_with_exponential_delay():
    invoked = []

    def failing_func():
        invoked.append(datetime.now())
        raise ValueError("error")

    interval = timedelta(milliseconds=10)
    retry = Retry(retriable_exceptions=[ValueError], interval=interval, interval_type=EXPONENTIAL)
    decorated = retry(failing_func)

    with pytest.raises(ValueError) as exception:
        decorated()

    assert str(exception.value) == "error"

    assert invoked[1] - invoked[0] >= timedelta(milliseconds=10)
    assert invoked[2] - invoked[1] >= timedelta(milliseconds=100)


def test_retry_should_raise_error_for_invalid_interval_type():
    with pytest.raises(ValueError) as exception:
        Retry(retriable_exceptions=[ValueError],
              interval=(timedelta(milliseconds=10)),
              interval_type='bogus')

    assert str(exception.value) == "Invalid interval type"
