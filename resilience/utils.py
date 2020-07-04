import threading


class RingBuffer:
    def __init__(self, size):
        self.__size = size
        self.__content = []

    def add(self, element):
        if len(self.__content) == self.__size:
            self.__content.pop(0)

        self.__content.append(element)

    def __iter__(self):
        return self.__content.__iter__()

    def clear(self):
        self.__content.clear()


class Counter:
    def __init__(self, initial_value=0):
        self.__value = initial_value
        self.__lock = threading.RLock()

    def increment(self):
        with self.__lock:
            self.__value += 1

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, current_value):
        with self.__lock:
            self.__value = current_value
