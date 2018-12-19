"""
Exports CallDebouncer enabling to debounce calls to function with same arguments.
"""

from collections import OrderedDict
from queue import Queue
from threading import Thread
import time


class CallArgs(object):
    """
    Hashable class to hold arbitrary hashable call arguments.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def call(self, callee):
        """
        Call callee with arguments class instance holds.
        """
        return callee(*self.args, **self.kwargs)

    def __hash__(self):
        return hash(tuple(self.args) + tuple(self.kwargs.items()))

    def __eq__(self, other):
        return (self.args == other.args) and (self.kwargs == other.kwargs)

    def __ne__(self, other):
        return not self == other


class CallDebouncer(object):
    """
    Delays calls to callee by given delay and ignores repeated calls with same arguments
    during delay time.
    """

    def __init__(self, callee, delay=0.1):
        self._callee = callee
        self._delay = delay

        self._call_times = OrderedDict()
        self._calls = Queue()
        self._worker = Thread(target=self._process_calls)
        self._worker.setDaemon(True)
        self._worker.start()


    def __call__(self, *args, **kwargs):
        self._calls.put((time.time(), CallArgs(*args, **kwargs)))

    def _process_calls(self):
        while True:
            submit_time, call_args = self._calls.get()
            self._remove_outdated(submit_time)

            if submit_time < self._call_times.get(call_args, 0):
                continue
            time_to_wait = submit_time + self._delay - time.time()
            if time_to_wait > 0:
                time.sleep(time_to_wait)

            # Remove item from call cache to put it at very end of OrderedDict.
            if call_args in self._call_times:
                self._call_times.pop(call_args)

            self._call_times[call_args] = time.time()

            call_args.call(self._callee)

    def _remove_outdated(self, submit_time):
        while self._call_times:
            cache_key, cache_time = next(iter(self._call_times.items())) # Pick first item
            if submit_time < cache_time:
                break
            self._call_times.pop(cache_key)
