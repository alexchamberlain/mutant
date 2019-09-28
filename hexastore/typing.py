import typing
from abc import abstractmethod
from typing import Any, ItemsView, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Union

from typing_extensions import Protocol

from .ast import IRI, Order, TripleStatus

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
# Hexastore = Any
Triple = Tuple[Term, Term, Term]
Index = OrderedMapping[Term, OrderedMapping[Term, OrderedMapping[Term, TripleStatus]]]
MutableIndex = MutableOrderedMapping[Term, MutableOrderedMapping[Term, MutableOrderedMapping[Term, TripleStatus]]]


class Hexastore(Protocol):
    def __len__(self) -> int:
        ...

    def index(self, triple: Triple) -> Optional[int]:
        ...

    def bulk_insert(self, triples: List[Triple]) -> None:
        ...

    def insert(self, s: Term, p: Term, o: Term) -> bool:
        ...

    def delete(self, s: Term, p: Term, o: Term) -> None:
        ...

    def terms(self) -> List[Term]:
        ...

    def triples(
        self, index: Optional[MutableIndex] = None, order: Optional[Tuple[Order, Order, Order]] = None
    ) -> Iterable[Triple]:
        ...
