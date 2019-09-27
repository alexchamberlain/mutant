import itertools
from typing import Callable, Tuple, TypeVar

from .model import Key

T = TypeVar("T")
U = TypeVar("U")


def triple_map(func: Callable[[U], T], triple: Tuple[U, U, U]) -> Tuple[T, T, T]:
    return func(triple[0]), func(triple[1]), func(triple[2])


def plot(store, filename):
    with open(filename, "w") as fo:
        fo.write(f"# {len(store)}\n")

        nodes = sorted({n for n in itertools.chain(store.spo, store.ops)}, key=Key)
        n_map = {s: i for i, s in enumerate(nodes)}

        fo.write("digraph G {\n")
        fo.write('    rankdir = "TB"\n')
        fo.write("    newrank = true\n")
        fo.write("    K = 1.5\n")
        fo.write("    node [shape=box]\n")

        for i, n in enumerate(nodes):
            fo.write(f'n{i} [label="{n}"]\n')

        for t in store.triples():
            fo.write(f'n{n_map[t[0]]} -> n{n_map[t[2]]} [label="{t[1]}"]\n')

        fo.write("}\n")
