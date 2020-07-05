"""
Retry
"""
import time
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import List, Type


class TimeInterval(ABC):  # pragma: no cover
    """
    Abstract time interval
    """

    @abstractmethod
    def sleep(self):
        """
        Sleep for this time interval
        """


class LinearTimeInterval(TimeInterval):
    """
    Linear time interval
    """

    def __init__(self, time_interval: timedelta):
        """
        Create new linear time interval
        :param time_interval:
        """
        self.__time_interval = time_interval

    def sleep(self):
        """
        Sleep for this time interval
        """
        time.sleep(self.__time_interval.total_seconds())


class ExponentialTimeInterval(TimeInterval):
    """
    Exponential time interval
    """

    def __init__(self, time_interval: timedelta):
        """
        Create new exponential time interval
        :param time_interval: timedelta base value
        """
        self.__time_interval = time_interval
        self.__sleeps = 1

    def sleep(self):
        """
        Sleep for this time interval

        The value grows exponentially for every invocation
        """
        interval_ms = self.__time_interval.total_seconds() * 1000
        sleep_ms = interval_ms ** self.__sleeps
        time.sleep(sleep_ms / 1000)
        self.__sleeps += 1


LINEAR = 'linear'
EXPONENTIAL = 'exponential'


class Retry:
    """
    Makes a function retriable
    """

    def __init__(self,
                 retriable_exceptions: List[Type[BaseException]],
                 attempts: int = 3,
                 interval: timedelta = timedelta(milliseconds=500),
                 interval_type: str = LINEAR):
        """
        Creates a new retry instance
        :param retriable_exceptions: List[BaseException] exceptions to retry for
        :param attempts: int number of retries (default: 3)
        :param interval: timedelta time interval between successive retries (default: 500ms)
        :param interval_type: string type of interval (default: LINEAR)
        """
        self.__retriable_exceptions = retriable_exceptions
        self.__attempts = attempts
        self.__interval = interval

        if interval_type not in (LINEAR, EXPONENTIAL):
            raise ValueError("Invalid interval type")

        self.__interval_type = interval_type

    def __call__(self, func):
        def wrapped_func(*args, **kwargs):
            time_interval = self.__get_time_interval()
            for attempt in range(1, self.__attempts + 1):
                # noinspection PyBroadException
                try:
                    val = func(*args, **kwargs)
                    return val
                except BaseException as exception:  # pylint: disable=broad-except
                    if not any([isinstance(exception, retriable_exception)
                                for retriable_exception in self.__retriable_exceptions]):
                        raise exception

                    time_interval.sleep()

                    if attempt == self.__attempts:
                        raise exception

        return wrapped_func

    def __get_time_interval(self):  # pylint: disable=inconsistent-return-statements
        if self.__interval_type == LINEAR:
            return LinearTimeInterval(self.__interval)

        if self.__interval_type == EXPONENTIAL:
            return ExponentialTimeInterval(self.__interval)

        assert False  # pragma: no cover
