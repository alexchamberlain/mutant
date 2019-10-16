import os
import tempfile

import pytest

from hexastore import IRI, BlankNodeFactory, InMemoryHexastore
from hexastore.ast import Order, OrderCondition, Variable
from hexastore.disk import Builder, FileHandler
from hexastore.engine import execute
from hexastore.turtle import parse

DAVE_SMITH = IRI("http://example.com/dave-smith")
ERIC_MILLER = IRI("http://example.com/eric-miller")
ERIC_MILLER_MBOX = IRI("mailto:e.miller123(at)example")
W3 = IRI("http://example.com/w3")

TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

KNOWS = IRI("http://xmlns.com/foaf/0.1/knows")
MBOX = IRI("http://xmlns.com/foaf/0.1/mbox")
NAME = IRI("http://xmlns.com/foaf/0.1/name")
ORGANIZATION = IRI("https://schema.org/Organization")
PERSON = IRI("http://xmlns.com/foaf/0.1/Person")
TITLE = IRI("http://xmlns.com/foaf/0.1/title")
WORKS_FOR = IRI("https://schema.org/worksFor")


dir_path = os.path.dirname(os.path.realpath(__file__))


def from_file_to_tmp(from_file):

    blank_node_factory = BlankNodeFactory()
    store = InMemoryHexastore(blank_node_factory)

    with open(from_file, "r") as fo:
        parse(fo.read(), store.insert, blank_node_factory)

    fd, path = tempfile.mkstemp()
    os.close(fd)
    builder = Builder(path, store)
    builder.serialise()

    return path


@pytest.mark.disk
def test_triples():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler,
        [(Variable("s"), Variable("p"), Variable("o"))],
        [
            OrderCondition("s", Order.ASCENDING),
            OrderCondition("p", Order.ASCENDING),
            OrderCondition("o", Order.ASCENDING),
        ],
    )

    assert solutions == [
        {
            Variable("s"): IRI("http://www.w3.org/People/EM/contact#me"),
            Variable("p"): IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            Variable("o"): IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
        },
        {
            Variable("s"): IRI("http://www.w3.org/People/EM/contact#me"),
            Variable("p"): IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
            Variable("o"): "Eric Miller",
        },
        {
            Variable("s"): IRI("http://www.w3.org/People/EM/contact#me"),
            Variable("p"): IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox"),
            Variable("o"): IRI("mailto:e.miller123(at)example"),
        },
        {
            Variable("s"): IRI("http://www.w3.org/People/EM/contact#me"),
            Variable("p"): IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle"),
            Variable("o"): "Dr.",
        },
        {
            Variable("s"): IRI("https://alexchamberlain.co.uk/#me"),
            Variable("p"): IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            Variable("o"): IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
        },
        {
            Variable("s"): IRI("https://alexchamberlain.co.uk/#me"),
            Variable("p"): IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
            Variable("o"): "Alex Chamberlain",
        },
        {
            Variable("s"): IRI("https://alexchamberlain.co.uk/#me"),
            Variable("p"): IRI("https://schema.org/name"),
            Variable("o"): "Alex Chamberlain",
        },
    ]

    # In this case, we ask for all triples, so we should visit each triple once.
    assert stats.triples_visited == len(solutions)


@pytest.mark.disk
def test_types():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler,
        [
            (
                Variable("s"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
            )
        ],
        [OrderCondition("s", Order.ASCENDING)],
    )

    assert solutions == [
        {Variable("s"): IRI("http://www.w3.org/People/EM/contact#me")},
        {Variable("s"): IRI("https://alexchamberlain.co.uk/#me")},
    ]

    assert stats.triples_visited == len(solutions)


@pytest.mark.disk
def test_types_no_match():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler,
        [
            (
                Variable("s"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Organization"),
            )
        ],
        [OrderCondition("s", Order.ASCENDING)],
    )

    assert solutions == []

    assert stats.triples_visited == 0


@pytest.mark.disk
def test_person_by_fullName():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler,
        [
            (
                Variable("s"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
            ),
            (Variable("s"), IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"), Variable("fullName")),
        ],
        [OrderCondition("fullName", Order.ASCENDING)],
    )

    assert solutions == [
        {Variable("s"): IRI("https://alexchamberlain.co.uk/#me"), Variable("fullName"): "Alex Chamberlain"},
        {Variable("s"): IRI("http://www.w3.org/People/EM/contact#me"), Variable("fullName"): "Eric Miller"},
    ]

    assert stats.triples_visited == len(solutions) * 2


@pytest.mark.disk
def test_no_variable():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler,
        [
            (
                IRI("https://alexchamberlain.co.uk/#me"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
            )
        ],
        [],
    )

    assert solutions == [{}]

    assert stats.triples_visited == len(solutions)


@pytest.mark.disk
def test_2_variables():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler, [(Variable("s"), IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), Variable("type"))], []
    )

    assert solutions == [
        {
            Variable("s"): IRI("http://www.w3.org/People/EM/contact#me"),
            Variable("type"): IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
        },
        {
            Variable("s"): IRI("https://alexchamberlain.co.uk/#me"),
            Variable("type"): IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
        },
    ]

    assert stats.triples_visited == len(solutions)


@pytest.mark.disk
def test_2_variables_no_results():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler, [(Variable("s"), IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#foobar"), Variable("type"))], []
    )

    assert solutions == []

    assert stats.triples_visited == 0


@pytest.mark.disk
def test_no_variable_false():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    solutions, stats = execute(
        handler,
        [
            (
                IRI("https://alexchamberlain.co.uk/#you"),
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"),
            )
        ],
        [],
    )

    assert solutions == []

    assert stats.triples_visited == len(solutions)
