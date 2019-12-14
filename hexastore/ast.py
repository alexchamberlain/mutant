import decimal
import enum
import functools
from typing import List, Optional

import attr

from _hexastore import IRI, BlankNode, LangTaggedString, TypedLiteral, Variable


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


# Reference: https://www.w3.org/TR/rdf-sparql-query/#modOrderBy
#   SPARQL also fixes an order between some kinds of RDF terms that would not otherwise be ordered:
#
#   (Lowest) no value assigned to the variable or expression in this solution.
#   Blank nodes
#   IRIs
#   RDF literals
#
# TODO: Improve ordering so that TypedLiterals are interspersed with literals that are stored
#   in native form.
TYPE_ORDER = [
    type(None),
    tuple,
    BlankNode,
    IRI,
    str,
    LangTaggedString,
    int,
    decimal.Decimal,
    float,
    TypedLiteral,
    Variable,
]

TYPE_ORDER_MAP = {k: i for i, k in enumerate(TYPE_ORDER)}
