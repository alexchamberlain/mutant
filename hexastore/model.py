import functools
import io
from typing import AbstractSet, Dict, List, Optional, Tuple, TypeVar, Union, overload

from immutables import Map

from .ast import TYPE_ORDER_MAP, Order, OrderCondition, Variable
from .typing import Term, Triple

T = TypeVar("T")


@functools.total_ordering
class Key:
    __slots__ = ["obj", "_type", "_order"]

    def __init__(self, obj: Term):
        self.obj = obj
        self._type = type(obj)

        try:
            self._order = TYPE_ORDER_MAP[self._type]
        except KeyError:
            raise TypeError(f"Unable to Key({self._type}: {self.obj})")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Key):
            return NotImplemented

        if self._type is not other._type:
            return False
        else:
            return self.obj == other.obj

    def __lt__(self, other: object) -> bool:
        """Implement self.obj < other.obj according to RDF rules"""

        if not isinstance(other, Key):
            return NotImplemented

        if self._type is not other._type:
            return self._order < other._order
        else:
            # assert isinstance(self.obj, type(other.obj))
            if isinstance(self.obj, tuple):
                for lhs, rhs in zip(self.obj, other.obj):
                    if lhs == rhs:
                        continue

                    return Key(lhs) < Key(rhs)
            else:
                return self.obj < other.obj

    __hash__ = None  # type: ignore


@functools.total_ordering
class Solution:
    def __init__(
        self,
        d: Union["Map[Variable, Term]", Dict[Variable, Term]],
        o: List[OrderCondition],
        triples: AbstractSet[Triple],
    ):
        self._d = d if isinstance(d, Map) else Map(d)
        self._o = o
        self._triples = triples

    def mutate(self, other: Union[Dict[Variable, Term], "Solution"]) -> "Solution":
        if isinstance(other, Solution):
            # self._d.update(other._d)
            triples = self._triples | other._triples

            other_d: Union["Map[Variable, Term]", Dict[Variable, Term]] = other._d
        else:
            other_d = other
            triples = self._triples

        with self._d.mutate() as mm:
            for k, v in other_d.items():
                if k in mm:
                    assert mm[k] == v
                    continue

                mm[k] = v

            d = mm.finish()

        return Solution(d, self._o, triples)

    @overload
    def get(self, key: Variable, default: Term) -> Term:
        pass

    @overload
    def get(self, key: Variable, default: Variable) -> Variable:
        pass

    @overload
    def get(self, key: Variable, default: None) -> Optional[T]:
        pass

    @overload
    def get(self, key: Variable) -> Optional[T]:
        pass

    def get(self, key: Variable, default: Optional[T] = None) -> Union[T, Term, None]:
        return self._d.get(key, default)

    def items(self) -> List[Tuple[Variable, Term]]:
        return sorted(self._d.items(), key=lambda x: x[0])

    def variables(self):
        return set(self._d.keys())

    @property
    def triples(self):
        return self._triples

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Solution):
            return self._d == other._d and self._triples == other._triples

        if isinstance(other, dict):
            return len(self._d) == len(other) and all(v == other[k] for k, v in self._d.items())

        return NotImplemented

    def __repr__(self) -> str:
        d = ",".join(f"{k!r}: {v!r}" for k, v in self._d.items())

        return f"Solution({{{d}}}, ...)"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Solution):
            return NotImplemented

        variables = set(self._d.keys())
        variables.update(other._d.keys())

        for v in self._o:
            var = Variable(v.variable_name)
            try:
                variables.remove(var)
            except KeyError:
                pass

            lhs = self.get(var)
            rhs = other.get(var)

            assert lhs is not None or rhs is not None

            if v.direction == Order.ASCENDING and Key(lhs) < Key(rhs):
                return True
            elif v.direction == Order.DESCENDING and Key(lhs) > Key(rhs):
                return True
            elif lhs == rhs:
                continue
            else:
                return False

        for var in sorted(variables):
            lhs = self.get(var)
            rhs = other.get(var)

            if Key(lhs) < Key(rhs):
                return True
            elif lhs == rhs:
                continue
            else:
                return False

        return False
