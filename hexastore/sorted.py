import bisect
import functools
import typing
from typing import (
    AbstractSet,
    Any,
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    ValuesView,
    cast,
    overload,
)

from .ast import Order
from .typing import Comparable, MutableOrderedMapping

T = typing.TypeVar("T")
U = typing.TypeVar("U", bound=Comparable)
V = typing.TypeVar("V")


class SortedList(Sequence[T], AbstractSet[T]):
    def __init__(self, iterable: Optional[Iterable[T]] = None, *, key: Optional[Callable[[T], U]] = None):
        if key is None:
            self.key = cast(Callable[[T], U], lambda x: x)
        else:
            self.key = key

        if iterable is None:
            self._l: List[T] = []
            self._keys: List[U] = []
        else:
            self._l: List[T] = sorted(iterable, key=self.key)
            self._keys: List[U] = [self.key(k) for k in self._l]

    def __repr__(self) -> str:
        return "SortedList({!r})".format(self._l)

    def __len__(self) -> int:
        return len(self._l)

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> List[T]:
        ...

    def __getitem__(self, x: Union[int, slice]) -> Union[T, List[T]]:
        return self._l[x]

    def __delitem__(self, index: int) -> None:
        del self._l[index]
        del self._keys[index]

    def delete(self, x: T) -> None:
        i = self.index(x)
        del self._l[i]
        del self._keys[i]

    def __iter__(self) -> Iterator[T]:
        return iter(self._l)

    def __reversed__(self) -> Iterator[T]:
        return reversed(self._l)

    def iter(self, order: Order = Order.ASCENDING) -> Iterator[T]:
        return [iter(self), reversed(self)][order]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SortedList):
            return self._l == other._l
        elif isinstance(other, list):
            return self._l == other
        else:
            return NotImplemented

    def insert(self, x: T) -> int:
        key = self.key(x)
        i = bisect.bisect(self._keys, key)
        self._l.insert(i, x)
        self._keys.insert(i, key)
        return i

    def index(self, x: T, start: int = 0, end: Optional[int] = None) -> int:
        if end is None:
            end = len(self._l)

        key = self.key(x)
        i = bisect.bisect_left(self._keys, key, lo=start, hi=end)
        if i != end and self[i] == x:
            return i

        raise ValueError

    def index_or_insert(self, x: T, hint: Optional[int] = 0) -> Tuple[int, bool]:
        end = len(self._l)
        key = self.key(x)

        if end == 0 or self._keys[-1] < key:
            self._l.append(x)
            self._keys.append(key)
            return end, True

        i = bisect.bisect_left(self._keys, key, lo=hint, hi=end)
        if i != end and self[i] == x:
            return i, False

        self._l.insert(i, x)
        self._keys.insert(i, key)
        return i, True

    def __contains__(self, x: Any) -> bool:
        end = len(self._l)
        key = self.key(x)
        i = bisect.bisect_left(self._keys, key, lo=0, hi=end)
        return i != end and self[i] == x

    def to_list(self) -> list:
        return self._l


class _SortedMappingValues(ValuesView[V]):
    def __init__(self, l: List[V]):
        self._l = l

    def __len__(self) -> int:
        return len(self._l)

    def __iter__(self) -> Iterator[V]:
        return iter(self._l)

    def __contains__(self, x: Any) -> bool:
        return x in self._l


class SortedMapping(MutableOrderedMapping[T, V]):
    def __init__(self, iterable: Optional[Iterable[Tuple[T, V]]] = None, *, key: Optional[Callable[[T], U]] = None):
        self._keys = SortedList(key=key)
        self._values: List[V] = []

        if isinstance(iterable, dict):
            self._keys = SortedList(iterable.keys(), key=key)
            self._values = [iterable[k] for k in self._keys]
        elif iterable is not None:
            keys, values = zip(*iterable)
            assert list(keys) == sorted(keys, key=key)
            self._keys = SortedList(keys, key=key)
            self._values = list(values)

    def __len__(self) -> int:
        return len(self._keys)

    def __repr__(self) -> str:
        return "SortedMapping({!r})".format({k: v for k, v in self.items()})

    def __iter__(self) -> Iterator[T]:
        return iter(self._keys)

    def keys(self) -> AbstractSet[T]:
        return self._keys

    def values(self) -> ValuesView[V]:
        return _SortedMappingValues(self._values)

    def items(self, order: Order = Order.ASCENDING) -> ItemsView[T, V]:
        return _SortedMappingItems(self, order)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SortedMapping):
            return self._keys == other._keys and self._values == other._values
        elif isinstance(other, dict):
            return self._keys == sorted(other.keys(), key=self._keys.key) and all(
                v == other[k] for k, v in zip(self._keys, self._values)
            )
        else:
            return NotImplemented

    def __ne__(self, other: Any) -> bool:
        return not (self == other)

    def __contains__(self, x: Any) -> bool:
        return x in self._keys

    def __getitem__(self, k: Union[Sequence[T], T]) -> Union[Sequence[Tuple[T, V]], V]:
        if isinstance(k, list) or isinstance(k, SortedList):
            output = []

            k_iter = iter(k)
            items_iter = iter(zip(self._keys, self._values))

            try:
                k_current = next(k_iter)
                items_current = next(items_iter)

                while True:
                    if self._keys.key(k_current) < self._keys.key(items_current[0]):
                        k_current = next(k_iter)
                    elif self._keys.key(k_current) > self._keys.key(items_current[0]):
                        items_current = next(items_iter)
                    else:
                        output.append((k_current, items_current[1]))
                        k_current = next(k_iter)
                        items_current = next(items_iter)
            except StopIteration:
                return output
        else:
            try:
                return self._values[self._keys.index(k)]
            except ValueError:
                raise KeyError(k)

    def __setitem__(self, k: T, v: V) -> None:
        i, inserted = self._keys.index_or_insert(k)
        if inserted:
            self._values.insert(i, v)
        else:
            self._values[i] = v

    def __delitem__(self, k: T) -> None:
        try:
            i = self._keys.index(k)
            del self._keys[i]
            del self._values[i]
        except ValueError:
            pass

    def get_or_set(self, k, factory, hint=0):
        i, inserted = self._keys.index_or_insert(k, hint=0)
        if inserted:
            v = factory()
            self._values.insert(i, v)
            return i, v
        else:
            return i, self._values[i]


class _SortedMappingItems(ItemsView[T, V]):
    def __init__(self, s: SortedMapping[T, V], order: Order):
        self._s = s
        self._order = order

    def __len__(self) -> int:
        return len(self._s)

    def __iter__(self) -> Iterator[Tuple[T, V]]:
        return [zip(self._s._keys, self._s._values), zip(reversed(self._s._keys), reversed(self._s._values))][
            self._order
        ]

    def __contains__(self, x: Any) -> bool:
        try:
            return self._s[x[0]] == x[1]
        except KeyError:
            raise KeyError(x[0])


class DefaultSortedMapping(SortedMapping[T, V]):
    def __init__(self, factory: Callable[[T], V], *, key: Optional[Callable[[T], U]] = None):
        super().__init__(key=key)
        self.factory = factory

    def __getitem__(self, k: Union[Sequence[T], T]) -> Union[Sequence[Tuple[T, V]], V]:
        if isinstance(k, list) or isinstance(k, SortedList):
            output = []

            hint = 0
            for kk in k:
                hint, value = self.get_or_set(kk, functools.partial(self.factory, kk))
                hint += 1
                output.append((kk, value))

            return output
        else:
            _, value = self.get_or_set(k, functools.partial(self.factory, k))
            return value
