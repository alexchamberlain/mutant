from unittest import mock

import pytest

from _hexastore import IRI, BlankNode


@pytest.mark.extension
def test_IRI():
    TITLE = IRI("http://xmlns.com/foaf/0.1/title")

    assert repr(TITLE) == "IRI(value='http://xmlns.com/foaf/0.1/title')"
    assert str(TITLE) == "http://xmlns.com/foaf/0.1/title"
    assert bytes(TITLE) == b"http://xmlns.com/foaf/0.1/title"

    assert TITLE == IRI("http://xmlns.com/foaf/0.1/title")
    assert TITLE != "http://xmlns.com/foaf/0.1/title"

    assert hash(TITLE)

    assert TITLE.value == "http://xmlns.com/foaf/0.1/title"


@pytest.mark.extension
def test_IRI_poor_value():
    with pytest.raises(TypeError):
        IRI(42)


@pytest.mark.extension
def test_IRI_mutation():
    TITLE = IRI("http://xmlns.com/foaf/0.1/title")

    with pytest.raises(AttributeError):
        TITLE.value = "http://xmlns.com/foaf/0.1/title2"


@pytest.mark.ast
def test_BlankNode():
    factory1 = mock.sentinel.factory1
    factory2 = mock.sentinel.factory2

    node1 = BlankNode(1, factory1)
    node2 = BlankNode(2, factory1)
    node3 = BlankNode(1, factory2)

    assert node1 != node2
    assert node1 != node3

    assert str(node1)
    assert repr(node1)
    assert hash(node1)
