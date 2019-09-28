import itertools
import logging
from typing import Any, List

from .ast import Order
from .memory import InMemoryHexastore, TrunkPayload, VersionedInMemoryHexastore, _ListAdapter
from .model import Key
from .sorted import SortedList, SortedMapping
from .typing import Triple

logger = logging.getLogger(__name__)


class BulkInserter:
    def __init__(self, underlying: VersionedInMemoryHexastore):
        self.underlying = underlying
        self.blank_node_factory = underlying.blank_node_factory
        self.overlay = InMemoryHexastore(self.blank_node_factory)

        self.spo = _MergedTrunk(self.underlying.spo, self.overlay.spo)
        self.pos = _MergedTrunk(self.underlying.pos, self.overlay.pos)
        self.osp = _MergedTrunk(self.underlying.osp, self.overlay.osp)
        self.sop = _MergedTrunk(self.underlying.sop, self.overlay.sop)
        self.ops = _MergedTrunk(self.underlying.ops, self.overlay.ops)
        self.pso = _MergedTrunk(self.underlying.pso, self.overlay.pso)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            return

        if len(self.overlay):
            self.underlying.bulk_insert(list(self.overlay.triples()))

    def __repr__(self):
        return f"<BulkInserter({id(self)})>"

    def triples(self):
        return SortedList(list(self.underlying.triples()) + list(self.overlay.triples()), key=Key)

    def insert(self, s, p, o):
        if (s, p, o) in self.underlying:
            return False

        return self.overlay.insert(s, p, o)

    def bulk_insert(self, triples: List[Triple]) -> None:
        return self.overlay.bulk_insert(triples)

    def __contains__(self, triple: Triple) -> bool:
        return triple in self.overlay or triple in self.underlying


class _MergedTrunk:
    def __init__(self, underlying, overlay):
        self._underlying = underlying
        self._overlay = overlay

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, term):
        return _MergedBranch(self._underlying[term], self._overlay[term])

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __iter__(self):
        return iter(self.keys())

    def __eq__(self, other: Any) -> bool:
        keys, values = zip(*self.items())
        if isinstance(other, SortedMapping):
            return keys == other._keys and values == other._values
        elif isinstance(other, dict):
            return list(keys) == sorted(other.keys(), key=Key) and all(v == other[k] for k, v in zip(keys, values))
        else:
            return NotImplemented

    def keys(self):
        return [k for k, _ in self.items()]

    def values(self):
        return [v for _, v in self.items()]

    def items(self, order=Order.ASCENDING):
        assert order == Order.ASCENDING

        k_under_iter, k_over_iter = iter(self._underlying.items()), iter(self._overlay.items())
        k_under_value, k_over_value = next(k_under_iter, None), next(k_over_iter, None)

        while k_under_value is not None and k_over_value is not None:
            if k_under_value[0] == k_over_value[0]:
                value = _MergedBranch(k_under_value[1], k_over_value[1])
                yield k_under_value[0], TrunkPayload(value, k_under_value[1].n + k_over_value[1].n)

                k_under_value = next(k_under_iter, None)
                k_over_value = next(k_over_iter, None)
            elif Key(k_under_value[0]) < Key(k_over_value[0]):
                yield k_under_value[0], TrunkPayload(_MergedBranch(k_under_value[1], {}), k_under_value[1].n)

                k_under_value = next(k_under_iter, None)
            else:
                yield k_over_value

                k_over_value = next(k_over_iter, None)

        #  Flush remaining tuples
        if k_under_value is not None:
            yield k_under_value[0], TrunkPayload(_MergedBranch(k_under_value[1], {}), k_under_value[1].n)

        for k, v in k_under_iter:
            yield k, TrunkPayload(_MergedBranch(v, {}), v.n)

        if k_over_value is not None:
            yield k_over_value

        for k, v in k_over_iter:
            yield k, v


class _MergedBranch:
    def __init__(self, underlying, overlay):
        self._underlying = underlying
        self._overlay = overlay

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, term):
        return self._merge_leaf(self._underlying[term], self._overlay[term])

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __iter__(self):
        return iter(self.keys())

    def __eq__(self, other: Any) -> bool:
        keys, values = zip(*self.items())
        if isinstance(other, SortedMapping):
            return keys == other._keys and values == other._values
        elif isinstance(other, dict):
            return list(keys) == sorted(other.keys(), key=Key) and all(v == other[k] for k, v in zip(keys, values))
        else:
            return NotImplemented

    def keys(self):
        return [k for k, _ in self.items()]

    def values(self):
        return [v for _, v in self.items()]

    def items(self, order=Order.ASCENDING):
        assert order == Order.ASCENDING

        k_under_iter, k_over_iter = iter(self._underlying.items()), iter(self._overlay.items())
        k_under_value, k_over_value = next(k_under_iter, None), next(k_over_iter, None)

        while k_under_value is not None and k_over_value is not None:
            if k_under_value[0] == k_over_value[0]:
                value = self._merge_leaf(k_under_value[1], k_over_value[1])
                yield k_under_value[0], value

                k_under_value = next(k_under_iter, None)
                k_over_value = next(k_over_iter, None)
            elif Key(k_under_value[0]) < Key(k_over_value[0]):
                yield k_under_value[0], _ListAdapter(SortedList(k_under_value[1].iter(order), key=Key))

                k_under_value = next(k_under_iter, None)
            else:
                yield k_over_value

                k_over_value = next(k_over_iter, None)

        #  Flush remaining tuples
        if k_under_value is not None:
            yield k_under_value[0], _ListAdapter(SortedList(k_under_value[1].iter(order), key=Key))

        for k, v in k_under_iter:
            yield k, _ListAdapter(SortedList(v.iter(order), key=Key))

        if k_over_value is not None:
            yield k_over_value

        yield from k_over_iter

    def _merge_leaf(self, k_under_value, k_over_value):
        return _ListAdapter(SortedList(itertools.chain(k_under_value.iter(), k_over_value.iter()), key=Key))
