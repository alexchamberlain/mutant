import itertools
from typing import Any, Callable, Iterable

from .ast import Variable
from .model import Solution


class Count:
    def __init__(self, output_variable: Variable):
        self._v = output_variable

    def __call__(self, key, subsolutions):
        return key.mutate({self._v: sum(1 for _ in subsolutions)})


class Generic:
    def __init__(self, input_variable: Variable, function: Callable[[Any], Any], output_variable: Variable):
        self._iv = input_variable
        self._f = function
        self._ov = output_variable

    def __call__(self, key, subsolutions):
        return key.mutate({self._ov: self._f(s.get(self._iv) for s in subsolutions)})


class Sample:
    def __init__(self, input_variable: Variable, output_variable: Variable):
        self._iv = input_variable
        self._ov = output_variable

    def __call__(self, key, subsolutions):
        return key.mutate({self._ov: next(subsolutions).get(self._iv)})


class Multi:
    def __init__(self, functions: Callable[[Solution, Iterable[Solution], Solution], Any]):
        self._f = functions

    def __call__(self, key, subsolutions):
        for f, s in zip(self._f, itertools.tee(subsolutions, len(self._f))):
            key = f(key, s)

        return key
