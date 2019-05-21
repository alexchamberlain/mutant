import sys
import contextlib

import click

from hexastore import generic_rule, turtle, turtle_serialiser
from hexastore.ast import IRI
from hexastore.memory import InMemoryHexastore
from hexastore.forward_reasoner import ForwardReasoner


@click.group()
def cli():
    pass


@cli.command()
@click.option("-n", "--namespace", type=(str, str), multiple=True)
@click.argument("filenames", nargs=-1)
@click.argument("output", nargs=1)
def reason(namespace, filenames, output):
    store = InMemoryHexastore()
    reasoner = ForwardReasoner(store)

    for filename in filenames:
        if filename.endswith("ttl"):
            with open(filename) as fo:
                turtle.parse(fo.read(), lambda s, p, o: reasoner.insert(s, p, o, 1))
        elif filename.endswith("mtt"):
            with open(filename) as fo:
                generic_rule.parse_and_register(fo.read(), reasoner)

    # with output
    # for t in store.triples():
    #     print(t)

    with smart_open(output) as fo:
        turtle_serialiser.serialise(store, fo, [(n, IRI(i)) for n, i in namespace])


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


if __name__ == "__main__":
    cli()