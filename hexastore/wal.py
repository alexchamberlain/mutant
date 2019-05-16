import enum
import math
import mmap
import os
import struct

import attr
import msgpack  # type: ignore

from . import ast


@attr.s
class Insert:
    triple = attr.ib()


@attr.s
class Delete:
    triple = attr.ib()


class ExtTypes(enum.IntEnum):
    INSERT = 0
    DELETE = 1
    TRIPLE = 2
    IRI = 3


def default(obj):
    packer = msgpack.Packer(default=default, use_bin_type=True, strict_types=True, autoreset=False)
    if isinstance(obj, tuple) and len(obj) == 3:
        packer.pack(obj[0])
        packer.pack(obj[1])
        packer.pack(obj[2])
        return msgpack.ExtType(ExtTypes.TRIPLE, packer.bytes())
    elif isinstance(obj, ast.IRI):
        packer.pack(obj.value)
        return msgpack.ExtType(ExtTypes.IRI, packer.bytes())
    elif isinstance(obj, Insert):
        packer.pack(obj.triple)
        return msgpack.ExtType(ExtTypes.INSERT, packer.bytes())
    elif isinstance(obj, Delete):
        packer.pack(obj.triple)
        return msgpack.ExtType(ExtTypes.DELETE, packer.bytes())

    raise TypeError("Unknown type: %r" % (obj,))


def ext_hook(code, data):
    # print(f"ext_hook {data}")
    unpacker = msgpack.Unpacker(ext_hook=ext_hook, raw=False)
    unpacker.feed(data)
    if code == ExtTypes.TRIPLE:
        return (unpacker.unpack(), unpacker.unpack(), unpacker.unpack())
    elif code == ExtTypes.IRI:
        return ast.IRI(unpacker.unpack())
    elif code == ExtTypes.INSERT:
        return Insert(unpacker.unpack())
    elif code == ExtTypes.DELETE:
        return Delete(unpacker.unpack())

    return msgpack.ExtType(code, data)


def pack(data):
    return msgpack.packb(data, default=default, use_bin_type=True, strict_types=True)


def unpack(packed):
    return msgpack.unpackb(packed, ext_hook=ext_hook, raw=False)


def _floor(offset):
    return math.floor(offset / mmap.PAGESIZE) * mmap.PAGESIZE


HEADER = struct.Struct("<II")


class WAL:
    def __init__(self, filename):
        M1 = mmap.PAGESIZE
        self._fd = os.open(filename, os.O_RDWR | os.O_CREAT)

        stat = os.fstat(self._fd)

        if stat.st_size == 0:
            os.ftruncate(self._fd, M1)
            self._size = M1
            self._len = 0
            self._offset = HEADER.size
            self._mmapper = mmap.mmap(self._fd, M1)
            HEADER.pack_into(self._mmapper, 0, self._len, self._offset)
            self._mmapper.flush(0, mmap.PAGESIZE)
        else:
            self._size = stat.st_size
            self._mmapper = mmap.mmap(self._fd, self._size)
            self._len, self._offset = HEADER.unpack_from(self._mmapper)

        # print(f"len = {self._len}, len = {self._offset}")

    def __len__(self):
        return self._len

    def _insert(self, action):
        packed = pack(action)
        start = self._offset
        end = self._offset + len(packed)
        if end > self._size:
            self._size += mmap.PAGESIZE
            os.ftruncate(self._fd, self._size)
            new_map = mmap.mmap(self._fd, self._size)
            self._mmapper.close()
            self._mmapper = new_map
        self._mmapper[self._offset : end] = packed

        self._len += 1
        self._offset = end

        HEADER.pack_into(self._mmapper, 0, self._len, self._offset)

        start_floor = _floor(start)
        end_floor = _floor(end - 1)

        if start_floor != 0:
            self._mmapper.flush(0, mmap.PAGESIZE)

        self._mmapper.flush(start_floor, mmap.PAGESIZE)

        if end_floor != start_floor:
            self._mmapper.flush(end_floor, mmap.PAGESIZE)

        return self._len - 1

    def insert(self, s, p, o):
        return self._insert(Insert((s, p, o)))

    def delete(self, s, p, o):
        return self._insert(Delete((s, p, o)))

    def __iter__(self):
        unpacker = msgpack.Unpacker(ext_hook=ext_hook, raw=False)
        unpacker.feed(self._mmapper[HEADER.size :])
        for i, unpacked in enumerate(unpacker):
            if i == self._len:
                return

            yield i, unpacked
