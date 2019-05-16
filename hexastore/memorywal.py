from .memory import InMemoryHexastore
from .wal import WAL, Insert, Delete
from .typing import Triple


class InMemoryHexastoreWithWal:
    def __init__(self, filename, store=None):
        self.memory = InMemoryHexastore() if store is None else store
        self.wal = WAL(filename)

        self.spo = self.memory.spo
        self.pos = self.memory.pos
        self.osp = self.memory.osp
        self.sop = self.memory.sop
        self.ops = self.memory.ops
        self.pso = self.memory.pso

        self.triples = self.memory.triples

        for i, a in self.wal:
            # print(f"ENTRY {a}")
            if isinstance(a, Insert):
                if a.triple[2] is None:
                    # print(f"Skipping {a}")
                    continue
                self.memory.insert(*a.triple, i)
            elif isinstance(a, Delete):
                self.memory.delete(*a.triple, i)

    def insert(self, s, p, o):
        log = self.wal.insert(s, p, o)
        self.memory.insert(s, p, o, log)

    def delete(self, s, p, o):
        log = self.wal.delete(s, p, o)
        self.memory.delete(s, p, o, log)

    def __contains__(self, triple: Triple):
        return triple in self.memory


def permanently_delete(input_filename, output_filename):
    input_store = InMemoryHexastoreWithWal(input_filename)
    output_store = InMemoryHexastoreWithWal(output_filename)

    for i, entry in input_store.wal:
        if isinstance(entry, Insert) and entry.triple in input_store:
            print(f"INSERT {entry.triple}")
            output_store.insert(*entry.triple)
        else:
            print(f"SKIPPED {entry}")
