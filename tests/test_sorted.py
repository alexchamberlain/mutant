import random

import hypothesis.strategies as st
import pytest
from hypothesis import given

from hexastore.sorted import Order, SortedList, SortedMapping


@pytest.mark.sorted
@pytest.mark.slow
@given(st.lists(st.integers()))
def test_SortedList(xs):
    ys = SortedList()

    for x in xs:
        ys.insert(x)

    assert ys == sorted(xs)

    zs = SortedList(xs)

    assert ys == zs


@pytest.mark.sorted
def test_SortedList_equal():
    assert SortedList([1, 2, 3, 4, 5]) != 42


@pytest.mark.sorted
def test_SortedList_index():
    xs = list(range(10))
    random.shuffle(xs)

    ys = SortedList(xs)
    assert all(ys.index(k) == k for k in range(10))

    del ys[3]
    assert ys == [0, 1, 2, 4, 5, 6, 7, 8, 9]


@pytest.mark.sorted
def test_SortedList_iter():
    assert all(x == y for x, y in zip(SortedList([1, 2, 3, 4, 5]).iter(Order.ASCENDING), range(1, 6)))
    assert all(x == y for x, y in zip(SortedList([1, 2, 3, 4, 5]).iter(Order.DESCENDING), reversed(range(1, 6))))


@pytest.mark.sorted
@pytest.mark.slow
@given(st.dictionaries(st.integers(), st.integers()))
def test_SortedMapping(xs):
    ys = SortedMapping()

    for k, v in xs.items():
        ys[k] = v

    assert ys == xs

    assert ys.keys() == sorted(xs.keys())
    assert all(v == xs[k] for k, v in zip(ys.keys(), ys.values()))
    assert all(v == xs[k] for k, v in ys.items())


@pytest.mark.sorted
def test_SortedMapping_simple():
    ys = SortedMapping()
    vv = ys.values()
    kv = ys.keys()
    iv = ys.items()

    assert len(ys) == len(vv) == len(kv) == len(iv)
    assert 81 not in vv

    for k in range(10):
        ys[k] = k * k

    assert ys == {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 5: 25, 6: 36, 7: 49, 8: 64, 9: 81}
    assert ys == SortedMapping({k: k * k for k in range(10)})

    assert len(ys) == len(vv) == len(kv) == len(iv)
    assert 81 in vv

    del ys[5]

    assert ys == {0: 0, 1: 1, 2: 4, 3: 9, 4: 16, 6: 36, 7: 49, 8: 64, 9: 81}


@pytest.mark.sorted
def test_SortedMapping_slice():
    ys = SortedMapping()

    for k in range(10):
        ys[k] = k * k

    ys[[3, 5]] == [(3, 9), (5, 25)]
