import functools
from typing import List, Dict, Union, Optional, Tuple, overload, TypeVar, AbstractSet

from .ast import TYPE_ORDER_MAP, Order, Variable, OrderCondition
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
    def __init__(self, d: Dict[Variable, Term], o: List[OrderCondition], triples: AbstractSet[Triple]):
        self._d = d
        self._o = o
        self._triples = triples

        assert all(len(t) == 3 for t in triples)

    def copy(self) -> "Solution":
        return Solution(self._d.copy(), self._o, self._triples)

    def update(self, other: Union[Dict[Variable, Term], "Solution"]) -> None:
        if isinstance(other, Solution):
            # self._d.update(other._d)
            self._triples.update(other._triples)

            other_d = other._d
        else:
            # self._d.update(other)
            other_d = other

        for k, v in other_d.items():
            if k in self._d:
                assert self._d[k] == v

            self._d[k] = v

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
        return self._d.keys()

    @property
    def triples(self):
        return self._triples

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Solution):
            return self._d == other._d and self._triples == other._triples
        else:
            return self._d == other

    def __repr__(self) -> str:
        return "Solution({!r}, ..., {!r})".format(self._d, self._triples)

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
