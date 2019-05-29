from decimal import Decimal
import io
import textwrap

import pytest

from hexastore.ast import IRI, LangTaggedString
from hexastore.model import Key
from hexastore.memory import InMemoryHexastore
from hexastore.diff_parser import parse

# from hexastore.turtle_serialiser import serialise


@pytest.mark.diff
def test_diff():
    document = """
        + <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf>
            <http://example.org/#green-goblin> .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1), lambda s, p, o: store.delete(s, p, o, 1))

    assert list(store.triples()) == [
        (
            IRI("http://example.org/#spiderman"),
            IRI("http://www.perceive.net/schemas/relationship/enemyOf"),
            IRI("http://example.org/#green-goblin"),
        )
    ]


@pytest.mark.diff
def test_diff_negative():
    document = """
        - <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf>
            <http://example.org/#green-goblin> .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1), lambda s, p, o: store.delete(s, p, o, 1))

    assert not store.spo[IRI("http://example.org/#spiderman")][
        IRI("http://www.perceive.net/schemas/relationship/enemyOf")
    ][IRI("http://example.org/#green-goblin")].inserted


@pytest.mark.diff
def test_diff_positive_and_negative():
    document = """
        - <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf>
            <http://example.org/#green-gblin> .
        + <http://example.org/#spiderman>
            <http://www.perceive.net/schemas/relationship/enemyOf>
            <http://example.org/#green-goblin> .
    """

    store = InMemoryHexastore()

    parse(document, lambda s, p, o: store.insert(s, p, o, 1), lambda s, p, o: store.delete(s, p, o, 1))

    assert not store.spo[IRI("http://example.org/#spiderman")][
        IRI("http://www.perceive.net/schemas/relationship/enemyOf")
    ][IRI("http://example.org/#green-gblin")].inserted
    assert store.spo[IRI("http://example.org/#spiderman")][IRI("http://www.perceive.net/schemas/relationship/enemyOf")][
        IRI("http://example.org/#green-goblin")
    ].inserted
