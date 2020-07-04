"""
Misc utilities
"""

import threading


class RingBuffer:
    """
    Implementation of a ring buffer
    """

    def __init__(self, size):
        """
        Create a new ring buffer
        :param size: int size of the ring buffer
        """
        self.__size = size
        self.__content = []

    def add(self, element):
        """
        Add a new element to this ring buffer.

        Removes the earliest element to make space for this element if required.
        :param element: Any
        :return: None
        """
        if len(self.__content) == self.__size:
            self.__content.pop(0)

        self.__content.append(element)

    def __iter__(self):
        return self.__content.__iter__()

    def clear(self):
        """
        Clear the contents of this ring buffer
        :return:
        """
        self.__content.clear()


class Counter:
    """
    A thread-safe counter
    """

    def __init__(self, initial_value=0):
        """
        Create a new counter
        :param initial_value: int initial value of this counter (default: 0)
        """
        self.__value = initial_value
        self.__lock = threading.RLock()

    def increment(self):
        """
        Increment this counter by 1
        :return: int current value of this counter
        """
        with self.__lock:
            self.__value += 1

        return self.__value

    @property
    def value(self):
        """
        Current value of this counter
        :return: int
        """
        return self.__value

    @value.setter
    def value(self, current_value):
        """
        Set the current value of this counter
        :param current_value: int
        :return: None
        """
        with self.__lock:
            self.__value = current_value
