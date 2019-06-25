import logging
import sys
import time

from hexastore import generic_rule, turtle, turtle_serialiser
from hexastore.ast import IRI
from hexastore.default_forward_reasoner import default_forward_reasoner
from hexastore.memory import InMemoryHexastore
from hexastore.memorywal import InMemoryHexastoreWithWal
from hexastore.namespace import Namespace

base = """
    @prefix schema: <https://schema.org/> .
    @prefix example: <https://example.org/> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

    example:pebbles schema:name "Pebbles Flintstone" .
    example:bamn-bamn schema:name "Bamm-Bamm Rubble" .
    example:roxy schema:name "Roxy Rubble" ;
        schema:parent example:pebbles, example:bamn-bamn .
    example:chip schema:name "Chip Rubble" ;
        schema:parent example:pebbles, example:bamn-bamn .
"""

rules = """
    @prefix schema: <https://schema.org/> .

    ($child1 schema:parent $parent), ($child2 schema:parent $parent) st ($child1 is-not $child2)
        → ($child1 schema:sibling $child2) .
"""


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.interval = self.end - self.start


def _update_namespaces(namespaces, new_namespaces):
    for prefix, namespace in new_namespaces.items():
        if prefix not in namespaces:
            namespaces[prefix] = namespace
        elif namespaces[prefix] != namespace:
            logger.warn(f"Ignoring {prefix}: {namespace}; using {prefix}: {namespaces[prefix]}")


logger = logging.getLogger()
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# root.addHandler(handler)

store = InMemoryHexastoreWithWal("layers.wal")
reasoner = default_forward_reasoner(store)

namespaces = {}

try:
    with Timer() as t:
        generic_rule.parse_and_register(rules, reasoner)

        triples = []
        new_namespaces = turtle.parse(base, lambda s, p, o: triples.append((s, p, o)))

        _update_namespaces(namespaces, new_namespaces)
        reasoner.bulk_insert(triples)
finally:
    logger.info(f"Parsing took {t.interval} seconds.")

turtle_serialiser.serialise(store, sys.stdout, [(n.name, n.prefix) for n in namespaces.values()])

assert store.log_index() == 1, f"{store.log_index()} != 1"
