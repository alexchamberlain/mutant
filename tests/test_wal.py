import os
import tempfile

import pytest
from hypothesis import given
import hypothesis.strategies as st
import msgpack

from hexastore import ast
from hexastore.wal import pack, unpack, WAL, Insert, Delete


class Foo:
    pass


@pytest.mark.wal
def test_encode_triple():
    foo = ("hello", "world", "bar")
    assert foo == unpack(pack(foo))

    foo = ast.IRI("hello")
    assert foo == unpack(pack(foo))

    with pytest.raises(TypeError):
        pack(Foo())

    foo = msgpack.ExtType(42, b"foo")
    assert unpack(pack(foo)) == foo


@pytest.mark.wal
def test_wal_file():
    fd, tf = tempfile.mkstemp()
    os.close(fd)

    wal = WAL(tf)

    wal.insert("hello", "world", "bar")

    assert _actions(wal) == [Insert(("hello", "world", "bar"))]


@pytest.mark.wal
def test_wal_file_delete():
    fd, tf = tempfile.mkstemp()
    os.close(fd)

    wal = WAL(tf)

    wal.insert("hello", "world", "bar")
    wal.delete("hello", "world", "bar")

    assert _actions(wal) == [Insert(("hello", "world", "bar")), Delete(("hello", "world", "bar"))]


@pytest.mark.wal
def test_wal_file_large():
    fd, tf = tempfile.mkstemp()
    os.close(fd)

    wal = WAL(tf)

    for _ in range(1024):
        wal.insert("hello", "world", "bar")

    assert _actions(wal) == [Insert(("hello", "world", "bar"))] * 1024


@pytest.mark.wal
@given(st.lists(st.tuples(st.text(), st.text(), st.text())))
def test_hypothesis_wal(foo):
    fd, tf = tempfile.mkstemp()
    os.close(fd)

    wal = WAL(tf)

    for t in foo:
        wal.insert(*t)

    assert _actions(wal) == [Insert(t) for t in foo]


def _actions(wal):
    if len(wal) == 0:
        return []

    return list(tuple(zip(*wal))[1])
