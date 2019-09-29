from typing import Callable, Iterable, List, Optional, Tuple, Union

import attr

from .ast import IRI, Variable
from .model import Solution

TermPattern = Union[IRI, str, Variable]
TriplePattern = Tuple[TermPattern, TermPattern, TermPattern]


@attr.s(frozen=True)
class BGP:
    patterns: List[TriplePattern] = attr.ib()
    limit: Optional[int] = attr.ib(default=None)


@attr.s(frozen=True)
class Limit:
    patterns: List[BGP] = attr.ib()
    limit: Optional[int] = attr.ib(default=None)


@attr.s(frozen=True)
class LeftJoin:
    lhs: BGP = attr.ib()
    rhs: BGP = attr.ib()
    # filter


@attr.s(frozen=True)
class Filter:
    pattern: Union[BGP, LeftJoin] = attr.ib()
    filter: Callable[[Solution], bool] = attr.ib()


@attr.s(frozen=True)
class Project:
    variables: List[Variable] = attr.ib()
    pattern: Union[BGP, LeftJoin] = attr.ib()


@attr.s(frozen=True)
class Distinct:
    pattern: Union[BGP, LeftJoin, Project] = attr.ib()


@attr.s(frozen=True)
class Reduced:
    pattern: Union[BGP, LeftJoin, Project] = attr.ib()


# I think this can be used to implement Group, Aggregate and AggregateJoin
# TODO: Group by expression
@attr.s(frozen=True)
class GroupAggregate:
    variables: List[Variable] = attr.ib()
    function: Callable[[Iterable[Solution]], Solution] = attr.ib()

    pattern: Union[BGP] = attr.ib()
