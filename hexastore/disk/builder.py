import itertools
import mmap
import os
from collections import defaultdict

from ..ast import IRI, BlankNode
from .binary import HEADER, LENGTH_PREFIX, TERM, TERM_PAYLOAD, TRUNK_PAYLOAD


class Builder:
    def __init__(self, filename, store):
        M1 = 100 * 1024 * 1024

        self.fd = os.open(filename, os.O_RDWR | os.O_CREAT)
        os.ftruncate(self.fd, M1)

        self.mmapper = mmap.mmap(self.fd, M1)
        self.store = store

        self.next_array = HEADER.size
        self.array_offset = defaultdict(dict)

        self.n_triples = self.store.n_triples
        self.terms = store.terms

        self.term_map = {}

    def serialise(self):
        iri_start, string_start, string_offset = self._serialise_terms()

        remainder = self.next_array % 4
        if remainder:
            self.next_array += 4 - remainder

        spo_offset = self.next_array
        pos_offset = self._serialise(self.store.spo, self.store.sop)
        osp_offset = self._serialise(self.store.pos, self.store.pso)
        end_offset = self._serialise(self.store.osp, self.store.ops)

        HEADER.pack_into(
            self.mmapper,
            0,
            self.n_triples,
            iri_start,
            string_start,
            string_offset,
            spo_offset,
            len(self.store.spo),
            pos_offset,
            len(self.store.pos),
            osp_offset,
            len(self.store.osp),
        )
        os.ftruncate(self.fd, end_offset)

        os.close(self.fd)

    def _serialise_terms(self):
        iri_start = self.n_triples
        string_start = self.n_triples
        string_offset = 0

        t_offset = 0
        for i, t in enumerate(self.terms):
            if isinstance(t, tuple):
                t_offset += 1
            elif isinstance(t, BlankNode):
                self.term_map[t] = i + self.n_triples - t_offset

                iri_start += 1
                string_start += 1
            elif isinstance(t, IRI):
                self.term_map[t] = i + self.n_triples - t_offset

                b = t.value.encode()
                LENGTH_PREFIX.pack_into(self.mmapper, self.next_array, len(b))
                self.next_array += LENGTH_PREFIX.size
                self.mmapper[self.next_array : self.next_array + len(b)] = b
                self.next_array += len(b)

                string_start += 1
            elif isinstance(t, str):
                self.term_map[t] = i + self.n_triples - t_offset

                if string_offset == 0:
                    string_offset = self.next_array

                b = t.encode()
                LENGTH_PREFIX.pack_into(self.mmapper, self.next_array, len(b))
                self.next_array += LENGTH_PREFIX.size
                self.mmapper[self.next_array : self.next_array + len(b)] = b
                self.next_array += len(b)
            else:
                assert False, type(t)

        return iri_start, string_start, string_offset

    def _serialise(self, index, reverse_index):
        array = index.keys()
        term_offset = self._allocate_array(len(array), TERM.size)
        self._serialise_array(term_offset, array)

        payload_offset = self._allocate_array(len(array), TRUNK_PAYLOAD.size)

        for i, s in enumerate(array):
            if len(index[s]) == 1 and len(reverse_index[s]) == 1:
                po_offset = 0
                len_po = self._to_int(next(iter(index[s])))
                op_offset = 0
                len_op = self._to_int(next(iter(reverse_index[s])))
            elif len(index[s]) == 1:
                po_offset = 0
                p = next(iter(index[s]))
                len_po = self._to_int(p)

                op_offset = self._array(s, p, index[s][p], False)
                len_op = len(reverse_index[s])

                assert index[s][p] == reverse_index[s].keys()
            elif len(reverse_index[s]) == 1:
                op_offset = 0
                o = next(iter(reverse_index[s]))
                len_op = self._to_int(o)

                po_offset = self._array(s, o, reverse_index[s][o], True)
                len_po = len(index[s])

                assert reverse_index[s][o] == index[s].keys()
            else:
                len_po = len(index[s])
                len_op = len(reverse_index[s])
                po_offset = self._serialise_term(index, False, s)
                op_offset = self._serialise_term(reverse_index, True, s)

            TRUNK_PAYLOAD.pack_into(
                self.mmapper, payload_offset + i * TRUNK_PAYLOAD.size, po_offset, len_po, op_offset, len_op
            )

        return self.next_array

    def _serialise_term(self, index, reverse, s):
        array = index[s].keys()
        all_0 = all(len(index[s][p]) == 1 for p in array)

        if all_0:
            term_offset = self._allocate_array(len(array), TERM.size)
            self._serialise_array(term_offset, array)
            payload_offset = self._allocate_array(len(array), TERM.size)
            self._serialise_array(payload_offset, (next(index[s][p].iter()) for p in array))
            return term_offset + 1
        else:
            term_offset = self._allocate_array(len(array), TERM.size)
            self._serialise_array(term_offset, array)
            payload_offset = self._allocate_array(len(array), TERM_PAYLOAD.size)
            for j, p in enumerate(array):
                if len(index[s][p]) == 1:
                    o_offset = 0
                    o = next(iter(index[s][p]))
                    length = self._to_int(o)
                else:
                    o_offset = self._array(s, p, index[s][p], reverse)
                    length = len(index[s][p])

                TERM_PAYLOAD.pack_into(self.mmapper, payload_offset + j * TERM_PAYLOAD.size, o_offset, length)

            return term_offset

    def _allocate_array(self, length, element_size):
        offset = self.next_array
        self.next_array = offset + length * element_size
        return offset

    def _array(self, t1, t2, a, reverse):
        if reverse:
            t1, t2 = t2, t1

        try:
            x = self.array_offset[t1][t2]
            assert x[1] == a, (t1, t2)
            return x[0]
        except KeyError:
            self.array_offset[t1][t2] = (self._allocate_array(len(a), TERM.size), a)

            self._serialise_array(self.array_offset[t1][t2][0], a)

            return self.array_offset[t1][t2][0]

    def _serialise_array(self, offset, array):
        for k, o in enumerate(array):
            TERM.pack_into(self.mmapper, offset + k * TERM.size, self._to_int(o))

    def _to_int(self, term):
        if isinstance(term, tuple):
            return self.store.index(term)
        else:
            assert self.term_map[term] >= self.n_triples, (term, self.term_map[term], self.n_triples)
            return self.term_map[term]
