from typing import Union, Any, Tuple, Mapping, ItemsView, MutableMapping
import typing
from typing_extensions import Protocol
from abc import abstractmethod

from .ast import IRI, TripleStatus, Order

_C = typing.TypeVar("_C", bound="Comparable")


class Comparable(Protocol):
    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __lt__(self: _C, other: _C) -> bool:
        pass

    def __gt__(self: _C, other: _C) -> bool:
        return (not self < other) and self != other

    def __le__(self: _C, other: _C) -> bool:
        return self < other or self == other

    def __ge__(self: _C, other: _C) -> bool:
        return not self < other


T = typing.TypeVar("T")
U = typing.TypeVar("U", bound=Comparable)
V = typing.TypeVar("V")


class OrderedMapping(Mapping[T, V]):
    @abstractmethod
    def items(self, order: Order = Order.ASCENDING) -> ItemsView[T, V]:
        pass


class MutableOrderedMapping(OrderedMapping[T, V], MutableMapping[T, V]):
    pass


Term = Union[IRI, str]
Hexastore = Any
Triple = Tuple[Term, Term, Term]
Index = OrderedMapping[Term, OrderedMapping[Term, OrderedMapping[Term, TripleStatus]]]
MutableIndex = MutableOrderedMapping[Term, MutableOrderedMapping[Term, MutableOrderedMapping[Term, TripleStatus]]]
