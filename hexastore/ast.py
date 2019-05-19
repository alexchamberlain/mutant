import decimal
import enum
import functools
from typing import List, Optional

import attr


@functools.total_ordering
@attr.s(frozen=True, cmp=False, hash=True, repr=False)
class BlankNode:
    def __str__(self) -> str:
        return str(id(self))

    def __lt__(self, other: object) -> bool:
        if isinstance(other, BlankNode):
            return id(self) < id(other)
        else:
            return NotImplemented

    def __repr__(self):
        return f"BlankNode({id(self)})"


@functools.total_ordering
@attr.s(frozen=True, cmp=False, hash=True)
class IRI:
    value: str = attr.ib()

    def __str__(self) -> str:
        return self.value

    def __bytes__(self) -> bytes:
        return self.value.encode()

    def __lt__(self, other: object) -> bool:
        if isinstance(other, IRI):
            return self.value < other.value
        else:
            return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IRI):
            return False

        return self.value == other.value


@functools.total_ordering
@attr.s(frozen=True, cmp=False, hash=True)
class LangTaggedString:
    value: str = attr.ib()
    language: str = attr.ib()

    def __str__(self) -> str:
        return f'"{self.value}"@{self.language}'

    def __lt__(self, other: object) -> bool:
        if isinstance(other, LangTaggedString):
            if self.value == other.value:
                return self.language < other.language

            return self.value < other.value
        else:
            return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LangTaggedString):
            return False

        return self.value == other.value and self.language == other.language


@functools.total_ordering
@attr.s(frozen=True, cmp=False, hash=True)
class Variable:
    value: str = attr.ib()

    def __str__(self) -> str:
        return self.value

    def __bytes__(self) -> bytes:
        return self.value.encode()

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Variable):
            return self.value < other.value
        else:
            return NotImplemented

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variable):
            return False

        return self.value == other.value


class Order(enum.IntEnum):
    ASCENDING = 0
    DESCENDING = 1


@attr.s(frozen=True)
class OrderCondition:
    variable_name: str = attr.ib()
    direction: Order = attr.ib()


class Status(enum.IntEnum):
    INSERTED = 0
    DELETED = 1
    UNKNOWN = 2


@attr.s
class TripleStatus:
    statuses: List["TripleStatusItem"] = attr.ib()  #  list of TripleStatusItem

    @property
    def inserted(self) -> bool:
        if len(self.statuses) and self.statuses[-1].valid_to is None:
            return True
        return False


@attr.s
class TripleStatusItem:
    valid_from: Optional[int] = attr.ib(default=None)
    valid_to: Optional[int] = attr.ib(default=None)


#  TODO: Verify the following order
TYPE_ORDER = [tuple, BlankNode, IRI, str, LangTaggedString, int, decimal.Decimal, float, Variable, type(None)]
