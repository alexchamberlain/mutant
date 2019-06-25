import os
import tempfile

import pytest

from hexastore.memorywal import InMemoryHexastoreWithWal


@pytest.mark.memorywal
def test_memorywal():
    fd, tf = tempfile.mkstemp()
    os.close(fd)

    wal = InMemoryHexastoreWithWal(tf)

    wal.insert("hello", "world", "bar")

    wal2 = InMemoryHexastoreWithWal(tf)

    triples = list(wal2.triples())
    assert triples == [("hello", "world", "bar")]
    assert ("hello", "world", "bar") in wal2

    wal2.delete("hello", "world", "bar")

    wal3 = InMemoryHexastoreWithWal(tf)

    triples = list(wal3.triples())
    assert triples == []
