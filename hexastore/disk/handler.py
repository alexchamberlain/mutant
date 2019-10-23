import bisect
import decimal
import mmap
import os
from typing import Optional, Tuple

from ..ast import IRI, LangTaggedString, Order, TypedLiteral
from ..model import Key
from ..sorted import SortedList
from .binary import DOUBLE_PAYLOAD, HEADER, INT_PAYLOAD, LENGTH_PREFIX, TERM, TERM_PAYLOAD, TRUNK_PAYLOAD


def _get_offset(*args):
    for offset in args:
        if offset != 0:
            return offset

    assert False


class FileHandler:
    def __init__(self, filename, blank_node_factory):
        fd = os.open(filename, os.O_RDONLY)
        stat = os.fstat(fd)
        self.mmapper = mmap.mmap(fd, stat.st_size, prot=mmap.PROT_READ)
        self.blank_node_factory = blank_node_factory

        self._preload()

    def _preload(self):
        (
            self._n_triples,
            self._iri_start,
            self._string_start,
            self._string_offset,
            self._lang_tagged_string_start,
            self._lang_tagged_string_offset,
            self._int_start,
            self._int_offset,
            self._decimal_start,
            self._decimal_offset,
            self._float_start,
            self._float_offset,
            self._typed_literal_start,
            self._typed_literal_offset,
            self._n_terms,
            self._spo_offset,
            self._len_spo,
            self._pos_offset,
            self._len_pos,
            self._osp_offset,
            self._len_osp,
        ) = HEADER.unpack_from(self.mmapper)

        terms = []

        for i in range(self._iri_start - self._n_triples):
            terms.append(self.blank_node_factory())

        offset = HEADER.size
        end_offset = _get_offset(
            self._string_offset,
            self._lang_tagged_string_offset,
            self._int_offset,
            self._decimal_offset,
            self._float_offset,
            self._typed_literal_offset,
            self._spo_offset,
        )
        while offset < end_offset:
            if end_offset - offset < LENGTH_PREFIX.size:
                break
            length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
            offset += LENGTH_PREFIX.size
            if length == 0 or (end_offset - offset < length):
                break
            b = self.mmapper[offset : offset + length]
            terms.append(IRI(b.decode()))
            offset += length

        assert offset == self._string_offset or self._string_offset == 0

        end_offset = _get_offset(
            self._lang_tagged_string_offset,
            self._int_offset,
            self._decimal_offset,
            self._float_offset,
            self._typed_literal_offset,
            self._spo_offset,
        )
        if self._string_offset != 0:
            while offset < end_offset:
                if end_offset - offset < LENGTH_PREFIX.size:
                    break
                length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
                offset += LENGTH_PREFIX.size

                assert end_offset - offset >= length

                if offset > self._string_offset and length == 0:
                    break

                b = self.mmapper[offset : offset + length]
                terms.append(b.decode())
                offset += length

        assert offset == self._lang_tagged_string_offset or self._lang_tagged_string_offset == 0

        end_offset = _get_offset(
            self._int_offset, self._decimal_offset, self._float_offset, self._typed_literal_offset, self._spo_offset
        )
        if self._lang_tagged_string_offset != 0:
            while offset < end_offset:
                if end_offset - offset < LENGTH_PREFIX.size:
                    break
                length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
                offset += LENGTH_PREFIX.size

                assert end_offset - offset >= length

                if offset > self._lang_tagged_string_offset and length == 0:
                    break

                b = self.mmapper[offset : offset + length]
                value = b.decode()
                offset += length

                assert end_offset - offset >= LENGTH_PREFIX.size

                length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
                offset += LENGTH_PREFIX.size

                assert end_offset - offset >= length

                if offset > self._lang_tagged_string_offset and length == 0:
                    break

                b = self.mmapper[offset : offset + length]
                language = b.decode()
                offset += length

                terms.append(LangTaggedString(value, language))

        assert offset == self._int_offset or self._int_offset == 0

        end_offset = _get_offset(self._decimal_offset, self._float_offset, self._typed_literal_offset, self._spo_offset)
        if self._int_offset != 0:
            while offset < end_offset:
                if end_offset - offset < INT_PAYLOAD.size:
                    break
                value, = INT_PAYLOAD.unpack_from(self.mmapper, offset)
                offset += INT_PAYLOAD.size

                terms.append(value)

        assert offset == self._decimal_offset or self._decimal_offset == 0

        end_offset = _get_offset(self._float_offset, self._typed_literal_offset, self._spo_offset)
        if self._decimal_offset != 0:
            while offset < end_offset:
                if end_offset - offset < LENGTH_PREFIX.size:
                    break
                length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
                offset += LENGTH_PREFIX.size

                assert end_offset - offset >= length

                if offset > self._decimal_offset and length == 0:
                    break

                b = self.mmapper[offset : offset + length]
                terms.append(decimal.Decimal(b.decode()))
                offset += length

        assert offset == self._float_offset or self._float_offset == 0

        end_offset = _get_offset(self._typed_literal_offset, self._spo_offset)
        if self._float_offset != 0:
            while offset < end_offset:
                if end_offset - offset < DOUBLE_PAYLOAD.size:
                    break
                value, = DOUBLE_PAYLOAD.unpack_from(self.mmapper, offset)
                offset += DOUBLE_PAYLOAD.size

                terms.append(value)

        assert offset == self._typed_literal_offset or self._typed_literal_offset == 0

        end_offset = self._spo_offset
        if self._typed_literal_offset != 0:
            while offset < end_offset:
                if end_offset - offset < LENGTH_PREFIX.size:
                    break
                length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
                offset += LENGTH_PREFIX.size

                assert end_offset - offset >= length

                if offset > self._typed_literal_offset and length == 0:
                    break

                b = self.mmapper[offset : offset + length]
                value = b.decode()
                offset += length

                assert end_offset - offset >= LENGTH_PREFIX.size

                length, = LENGTH_PREFIX.unpack_from(self.mmapper, offset)
                offset += LENGTH_PREFIX.size

                assert end_offset - offset >= length

                if offset > self._typed_literal_offset and length == 0:
                    break

                b = self.mmapper[offset : offset + length]
                datatype = IRI(b.decode())
                offset += length

                terms.append(TypedLiteral(value, datatype))

        assert terms == sorted(terms, key=Key)

        self.terms = SortedList(terms, key=Key)

        self.spo = _FileHandlerTrunkMapping(
            self.mmapper, self._to_int, self._from_int, self._spo_offset, self._len_spo, False
        )
        self.pos = _FileHandlerTrunkMapping(
            self.mmapper, self._to_int, self._from_int, self._pos_offset, self._len_pos, False
        )
        self.osp = _FileHandlerTrunkMapping(
            self.mmapper, self._to_int, self._from_int, self._osp_offset, self._len_osp, False
        )
        self.sop = _FileHandlerTrunkMapping(
            self.mmapper, self._to_int, self._from_int, self._spo_offset, self._len_spo, True
        )
        self.pso = _FileHandlerTrunkMapping(
            self.mmapper, self._to_int, self._from_int, self._pos_offset, self._len_pos, True
        )
        self.ops = _FileHandlerTrunkMapping(
            self.mmapper, self._to_int, self._from_int, self._osp_offset, self._len_osp, True
        )

    def index(self, triple) -> Optional[int]:
        try:
            t_ = self._to_int_tuple(triple)
        except ValueError:
            return None

        ii = 0

        for s, po in self.spo._int_mapping.items():
            for p, oid in po.items():
                for o in oid:
                    if t_ == (s, p, o):
                        return ii

                    ii += 1

        return None

    def triples(self, index=None, order: Optional[Tuple[Order, Order, Order]] = None):
        assert order is None or len(order) == 3

        if index is None:
            index = self.spo

        if order is None:
            order = (Order.ASCENDING, Order.ASCENDING, Order.ASCENDING)

        for s, po in index.items(order=order[0]):
            for p, oid in po.items(order=order[1]):
                iterable = [oid, reversed(oid)][order[2]]
                for o in iterable:
                    yield (s, p, o)

    def _from_int(self, i):
        assert isinstance(i, int)
        if i < self._n_triples:
            ii = 0

            for s, po in self.spo._int_mapping.items():
                for p, oid in po.items():
                    for o in oid:
                        if i == ii:
                            return (self._from_int(s), self._from_int(p), self._from_int(o))

                        ii += 1

        return self.terms[i - self._n_triples]

    def _to_int_tuple(self, t):
        return tuple(map(self._to_int, t))

    def _to_int(self, term):
        if isinstance(term, tuple):
            return self.index(term)

        return self.terms.index(term) + self._n_triples

    def __contains__(self, triple):
        return triple[2] in self.spo[triple[0]][triple[1]]


class _FileHandlerTrunkMapping:
    def __init__(self, mmapper, to_int, from_int, term_offset, length, reverse):
        self._int_mapping = _FileHandlerTrunkIntMapping(mmapper, term_offset, length, reverse)
        self._to_int = to_int
        self._from_int = from_int

    def __len__(self):
        return len(self._int_mapping)

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __eq__(self, other):
        if not isinstance(other, dict):
            return NotImplemented

        if len(self) != len(other):
            return False

        try:
            return all(v == other[k] for k, v in self.items())
        except KeyError:
            return False

    def __contains__(self, triple):
        return triple[2] in self[triple[0]][triple[1]]

    def __getitem__(self, key):
        try:
            return _FileHandlerBranchMapping(self._int_mapping[self._to_int(key)], self._to_int, self._from_int)
        except ValueError:
            raise KeyError(key)

    def items(self, order=Order.ASCENDING):
        for k, v in self._int_mapping.items():
            yield self._from_int(k), _FileHandlerBranchMapping(v, self._to_int, self._from_int)


class _FileHandlerTrunkIntMapping:
    def __init__(self, mmapper, term_offset, length, reverse):
        payload_offset = term_offset + length * TERM.size

        self.mmapper = mmapper
        self.term_array = _TermSequence(mmapper, term_offset, length)
        self.payload_array = _FileHandlerSequence(mmapper, payload_offset, length, TRUNK_PAYLOAD)
        self.reverse = reverse

    def __len__(self):
        return len(self.term_array)

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __eq__(self, other):
        if not isinstance(other, dict):
            return NotImplemented

        if len(self) != len(other):
            return False

        try:
            return all(v == other[k] for k, v in self.items())
        except KeyError:
            return False

    def __getitem__(self, key):
        assert isinstance(key, int)
        i = self.term_array.index(key)
        return self._payload(i)

    def items(self, order=Order.ASCENDING):
        iterable, i, increment = [(self.term_array, 0, 1), (reversed(self.term_array), len(self.term_array) - 1, -1)][
            order
        ]
        for term in iterable:
            yield term, self._payload(i)
            i += increment

    def _payload(self, i):
        po_offset, len_po, op_offset, len_op = self.payload_array[i]

        if self.reverse:
            po_offset, op_offset = op_offset, po_offset
            len_po, len_op = len_op, len_po

        if po_offset == 0 and op_offset == 0:
            p = len_po
            o = len_op
            return _DictWrapper({p: [o]})
        elif po_offset == 0:
            return _DictWrapper({len_po: [o[0] for o in _FileHandlerSequence(self.mmapper, op_offset, len_op, TERM)]})
        elif op_offset == 0:
            o = len_op
            p_array = _FileHandlerSequence(self.mmapper, po_offset, len_po, TERM)
            return _DictWrapper({p[0]: [o] for p in p_array})
        else:
            return _FileHandlerBranchIntMapping(self.mmapper, po_offset, len_po)


class _DictWrapper:
    def __init__(self, d):
        self.d = d

    def __len__(self):
        return len(self.d)

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.d == other
        elif isinstance(other, _DictWrapper):
            return self.d == other.d
        else:
            return NotImplemented

    def __getitem__(self, k):
        return [vv for vv in self.d[k]]

    def items(self, order=Order.ASCENDING):
        iterable = self.d.items()
        if order == Order.DESCENDING:
            iterable = reversed(iterable)

        for k, v in iterable:
            yield k, v


class _FileHandlerBranchMapping:
    def __init__(self, int_mapping, to_int, from_int):
        self._int_mapping = int_mapping
        self._to_int = to_int
        self._from_int = from_int

    def __len__(self):
        return len(self._int_mapping)

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __eq__(self, other):
        if not isinstance(other, dict):
            return NotImplemented

        if len(self) != len(other):
            return False

        try:
            return all(v == other[k] for k, v in self.items())
        except KeyError:
            return False

    def __getitem__(self, term):
        try:
            return _IntSequenceAdaptor(self._int_mapping[self._to_int(term)], self._from_int)
        except ValueError:
            raise KeyError(term)

    def items(self, order=Order.ASCENDING):
        for k, v in self._int_mapping.items(order=order):
            yield self._from_int(k), _IntSequenceAdaptor(v, self._from_int)


class _FileHandlerBranchIntMapping:
    def __init__(self, mmapper, term_offset, length):
        assert 0 < term_offset < len(mmapper)

        self.mmapper = mmapper

        self.all_0 = bool(term_offset % 2)
        term_offset = term_offset - 1 if self.all_0 else term_offset
        payload_offset = term_offset + length * TERM.size

        self.term_array = _TermSequence(mmapper, term_offset, length)
        self.payload_array = _FileHandlerSequence(mmapper, payload_offset, length, TERM if self.all_0 else TERM_PAYLOAD)

    def __len__(self):
        return len(self.term_array)

    def __repr__(self):
        return "{{{}}}".format(", ".join("{!r}: {!r}".format(k, v) for k, v in self.items()))

    def __eq__(self, other):
        if not isinstance(other, dict):
            return NotImplemented

        if len(self) != len(other):
            return False

        try:
            return all(v == other[k] for k, v in self.items())
        except KeyError:
            return False

    def __getitem__(self, term):
        assert isinstance(term, int)
        index = self.term_array.index(term)
        return self._payload(index)

    def _payload(self, i):
        payload = self.payload_array[i]
        if self.all_0:
            return [p for p in payload]
        elif payload[0] == 0:
            return [payload[1]]
        else:
            return _TermSequence(self.mmapper, payload[0], payload[1])

    def items(self, order=Order.ASCENDING):
        iterable = [self.term_array, reversed(self.term_array)][order]
        for i, term in enumerate(iterable):
            i = len(self.term_array) - i - 1 if order == Order.DESCENDING else i
            yield term, self._payload(i)


class _TermSequence:
    def __init__(self, mmapper, offset, length):
        self._sequence = _FileHandlerSequence(mmapper, offset, length, TERM)

    def __len__(self):
        return len(self._sequence)

    def __repr__(self):
        return "[{}]".format(", ".join(v) for v in self)

    def __eq__(self, other):
        if not isinstance(other, list):
            return NotImplemented

        if len(self) != len(other):
            return False

        return all(v1 == v2 for v1, v2 in zip(self, other))

    def __contains__(self, x):
        try:
            self.index(x)
            return True
        except ValueError:
            return False

    def index(self, x):
        "Locate the leftmost value exactly equal to x"
        assert isinstance(x, int)
        return self._sequence.index((x,))

    def __getitem__(self, key):
        assert isinstance(key, int)
        return self._sequence[(key,)]

    def __iter__(self):
        for v in self._sequence:
            yield v[0]

    def __reversed__(self):
        for v in reversed(self._sequence):
            yield v[0]


class _FileHandlerSequence:
    def __init__(self, mmapper, offset, length, element_struct):
        assert 0 < offset < len(mmapper)

        self.mmapper = mmapper
        self.offset = offset
        self.length = length
        self.element_struct = element_struct

    def __len__(self):
        return self.length

    def __repr__(self):
        return "[{!r}]".format(", ".join(v for v in self))

    def __eq__(self, other):
        if not isinstance(other, list):
            return NotImplemented

        if len(self) != len(other):
            return False

        return all(v1 == v2 for v1, v2 in zip(self, other))

    def __contains__(self, x):
        try:
            self.index(x)
            return True
        except ValueError:
            return False

    def index(self, x):
        "Locate the leftmost value exactly equal to x"
        assert isinstance(x, tuple) and len(x) == len(self.element_struct.format) - 1
        i = bisect.bisect_left(self, x)
        if i != len(self) and self[i] == x:
            return i
        raise ValueError(x)

    def __getitem__(self, key):
        assert isinstance(key, int)
        assert key < self.length
        return self.element_struct.unpack_from(self.mmapper, self.offset + key * self.element_struct.size)

    def __iter__(self):
        offset = self.offset
        for key in range(self.length):
            yield self.element_struct.unpack_from(self.mmapper, offset)
            offset += self.element_struct.size

    def __reversed__(self):
        offset = self.offset + self.length * self.element_struct.size
        for key in range(self.length):
            offset -= self.element_struct.size
            yield self.element_struct.unpack_from(self.mmapper, offset)


class _IntSequenceAdaptor:
    def __init__(self, l, from_int):
        self._l = l
        self._from_int = from_int

    def __repr__(self):
        return repr(list(iter(self)))

    def __len__(self):
        return len(self._l)

    def __getitem__(self, i):
        return self._from_int(self._l[i])

    def __iter__(self):
        return map(self._from_int, self._l)

    def __reversed__(self):
        return map(self._from_int, reversed(self._l))

    def iter(self, order=Order.ASCENDING, triple_counter=None):
        iterable = [self._l, reversed(self._l)][order]
        for v in iterable:
            if triple_counter:
                triple_counter()

            yield self._from_int(v)

    def __eq__(self, other):
        return len(self._l) == len(other) and all(self._from_int(x) == y for x, y in zip(self._l, other))
