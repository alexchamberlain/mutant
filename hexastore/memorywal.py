from .memory import VersionedInMemoryHexastore
from .typing import Triple
from .wal import WAL, BulkInsert, Delete, Insert


class InMemoryHexastoreWithWal:
    def __init__(self, filename, store=None):
        self.memory = VersionedInMemoryHexastore() if store is None else store
        self.wal = WAL(filename)

        self.spo = self.memory.spo
        self.pos = self.memory.pos
        self.osp = self.memory.osp
        self.sop = self.memory.sop
        self.ops = self.memory.ops
        self.pso = self.memory.pso

        self.triples = self.memory.triples
        self.terms = self.memory.terms

        for i, a in self.wal:
            if isinstance(a, Insert):
                self.memory.insert(*a.triple, i)
            elif isinstance(a, BulkInsert):
                self.memory.bulk_insert(a.triples, i)
            elif isinstance(a, Delete):
                self.memory.delete(*a.triple, i)

    def bulk_insert(self, triples):
        log = self.wal.bulk_insert(triples)
        self.memory.bulk_insert(triples, log)

    def insert(self, s, p, o):
        log = self.wal.insert(s, p, o)
        self.memory.insert(s, p, o, log)

    def delete(self, s, p, o):
        log = self.wal.delete(s, p, o)
        self.memory.delete(s, p, o, log)

    def __contains__(self, triple: Triple):
        return triple in self.memory

    def log_index(self):
        return len(self.wal)


def permanently_delete(input_filename, output_filename):
    input_store = InMemoryHexastoreWithWal(input_filename)
    output_store = InMemoryHexastoreWithWal(output_filename)

    for i, entry in input_store.wal:
        if isinstance(entry, Insert) and entry.triple in input_store:
            output_store.insert(*entry.triple)
