"""Bisection algorithms."""

from typing import Sequence, TypeVar, Optional, Callable, cast
from .typing import Comparable

T = TypeVar("T")
U = TypeVar("U", bound=Comparable)


def bisect_left(
    a: Sequence[T], x: T, lo: int = 0, hi: Optional[int] = None, key: Optional[Callable[[T], U]] = None
) -> int:
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e < x, and all e in
    a[i:] have e >= x.  So if x already appears in the list, a.insert(x) will
    insert just before the leftmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if key is None:
        key = cast(Callable[[T], U], lambda x: x)

    if lo < 0:
        raise ValueError("lo must be non-negative")

    if hi is None:
        hi = len(a)

    while lo < hi:
        mid = (lo + hi) // 2
        if key(a[mid]) < key(x):
            lo = mid + 1
        else:
            hi = mid

    return lo


def bisect_right(
    a: Sequence[T], x: T, lo: int = 0, hi: Optional[int] = None, key: Optional[Callable[[T], U]] = None
) -> int:
    """Return the index where to insert item x in list a, assuming a is sorted.

    The return value i is such that all e in a[:i] have e <= x, and all e in
    a[i:] have e > x.  So if x already appears in the list, a.insert(x) will
    insert just after the rightmost x already there.

    Optional args lo (default 0) and hi (default len(a)) bound the
    slice of a to be searched.
    """

    if key is None:
        key = cast(Callable[[T], U], lambda x: x)

    if lo < 0:
        raise ValueError("lo must be non-negative")

    if hi is None:
        hi = len(a)

    while lo < hi:
        mid = (lo + hi) // 2
        if key(x) < key(a[mid]):
            hi = mid
        else:
            lo = mid + 1
    return lo


bisect = bisect_right
