from datetime import timedelta, datetime
from threading import RLock

from .exceptions import CallNotAllowedException
from .utils import RingBuffer, Counter

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"

SUCCESS = True
FAILURE = False


class CircuitBreaker:
    def __init__(self, name, sliding_window_size=10, trip_threshold=0.5, trip_duration=timedelta(seconds=5),
                 allowed_calls_in_half_open=2, allowed_exceptions=None):

        if allowed_exceptions is None:
            allowed_exceptions = []

        self.__name = name
        self.__sliding_window_size = sliding_window_size
        self.__trip_threshold = trip_threshold
        self.__trip_duration = trip_duration
        self.__allowed_calls_in_half_open = allowed_calls_in_half_open
        self.__allowed_exceptions = allowed_exceptions

        self.state = CLOSED

        self.__executions = RingBuffer(10)
        self.__state_transition_lock = RLock()
        self.__calls_since_half_open = Counter(0)

    def __call__(self, func):
        def wrapped_func(*args, **kwargs):
            if self.state == OPEN:
                raise CallNotAllowedException("Circuit breaker is open")

            try:
                value = func(*args, **kwargs)
                self.__handle_call_success()
                return value
            except BaseException as e:
                self.__handle_call_failure(e)
                raise e

        return wrapped_func

    def __handle_call_failure(self, e):
        ignore = any([isinstance(e, exception) for exception in self.__allowed_exceptions])

        if ignore:
            self.__handle_call_success()
            return

        with self.__state_transition_lock:
            if self.state == HALF_OPEN:
                self.state = OPEN
            elif self.state == CLOSED:
                self.__executions.add(FAILURE)

                failures = sum([1 for result in self.__executions if result == FAILURE])

                if failures / self.__sliding_window_size > self.__trip_threshold:
                    self.state = OPEN

    def __handle_call_success(self):
        with self.__state_transition_lock:
            if self.state == CLOSED:
                self.__executions.add(SUCCESS)
            elif self.state == HALF_OPEN:
                self.__calls_since_half_open.increment()

            if self.__calls_since_half_open.value > self.__allowed_calls_in_half_open:
                self.reset()


    @property
    def state(self):
        with self.__state_transition_lock:
            if self.__state == OPEN:
                if datetime.now() - self.__state_transitioned_at > self.__trip_duration:
                    self.state = HALF_OPEN

        return self.__state

    @state.setter
    def state(self, current_state):
        self.__state = current_state
        self.__state_transitioned_at = datetime.now()

        if current_state == HALF_OPEN:
            self.__calls_since_half_open.value = 0

    def reset(self):
        self.__calls_since_half_open = 0
        self.state = CLOSED
        self.__executions.clear()
