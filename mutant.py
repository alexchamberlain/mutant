import sys
import contextlib
import logging
from typing import Dict
import time

import click

from hexastore import generic_rule, turtle, turtle_serialiser
from hexastore.ast import IRI
from hexastore.namespace import Namespace
from hexastore.memory import VersionedInMemoryHexastore
from hexastore.default_forward_reasoner import default_forward_reasoner

logger = logging.getLogger(__name__)


root = logging.getLogger()
root.setLevel(logging.DEBUG)

# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# handler.setFormatter(formatter)
# root.addHandler(handler)


@click.group()
@click.option("-l", "--log-file")
def cli(log_file):
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        root.addHandler(handler)


@cli.command()
@click.option("-n", "--namespace", type=(str, str), multiple=True)
@click.argument("filenames", nargs=-1)
@click.argument("output", nargs=1)
def cat(namespace, filenames, output):
    store = VersionedInMemoryHexastore()

    namespaces: Dict[str, Namespace] = {n: Namespace(n, IRI(i)) for n, i in namespace}

    try:
        with Timer() as t:
            for filename in filenames:
                if filename.endswith("ttl") or filename.endswith("nt"):
                    triples = []
                    with open(filename) as fo:
                        new_namespaces = turtle.parse(fo.read(), lambda s, p, o: triples.append((s, p, o)))

                    _update_namespaces(namespaces, new_namespaces)
                    store.bulk_insert(triples, 1)
                else:
                    raise RuntimeError(f"Unknown file {filename}")
    finally:
        logger.info(f"Parsing took {t.interval} seconds.")

    try:
        with Timer() as t:
            print(f"# Triples {len(store)}")

            with smart_open(output) as fo:
                turtle_serialiser.serialise(store, fo, [(n.name, n.prefix) for n in namespaces.values()])
    finally:
        logger.info(f"Serialisation took {t.interval} seconds.")


@cli.command()
@click.option("-n", "--namespace", type=(str, str), multiple=True)
@click.argument("filenames", nargs=-1)
@click.argument("output", nargs=1)
def reason(namespace, filenames, output):
    store = VersionedInMemoryHexastore()
    reasoner = default_forward_reasoner(store)

    namespaces: Dict[str, Namespace] = {n: Namespace(n, IRI(i)) for n, i in namespace}

    try:
        with Timer() as t:
            for filename in filenames:
                if filename.endswith("ttl") or filename.endswith("nt"):
                    triples = []
                    with open(filename) as fo:
                        new_namespaces = turtle.parse(fo.read(), lambda s, p, o: triples.append((s, p, o)))

                    _update_namespaces(namespaces, new_namespaces)
                    reasoner.bulk_insert(triples, 1)
                elif filename.endswith("mtt"):
                    with open(filename) as fo:
                        generic_rule.parse_and_register(fo.read(), reasoner)
                else:
                    raise RuntimeError(f"Unknown file {filename}")
    finally:
        logger.info(f"Parsing took {t.interval} seconds.")

    try:
        with Timer() as t:
            print(f"# Triples {len(store)}")

            with smart_open(output) as fo:
                turtle_serialiser.serialise(store, fo, [(n.name, n.prefix) for n in namespaces.values()])
    finally:
        logger.info(f"Serialisation took {t.interval} seconds.")


def _update_namespaces(namespaces, new_namespaces):
    for prefix, namespace in new_namespaces.items():
        if prefix not in namespaces:
            namespaces[prefix] = namespace
        elif namespaces[prefix] != namespace:
            logger.warn(f"Ignoring {prefix}: {namespace}; using {prefix}: {namespaces[prefix]}")


@contextlib.contextmanager
def smart_open(filename=None):
    if filename and filename != "-":
        fh = open(filename, "w")
    else:
        fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdout:
            fh.close()


class Timer:
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start


if __name__ == "__main__":
    cli()
