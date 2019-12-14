from unittest import mock

import pytest

from _hexastore import IRI, BlankNode, LangTaggedString, TypedLiteral, Variable


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


@pytest.mark.extension
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


@pytest.mark.extension
def test_LangTaggedString():
    str1 = LangTaggedString("foo", "en")
    str2 = LangTaggedString("foo", "en")
    str3 = LangTaggedString("foo", "de")
    str4 = LangTaggedString("bar", "en")

    assert str1 == str2
    assert str1 != str3
    assert str1 != str4

    assert str3 < str1
    assert str1 > str3


@pytest.mark.extension
def test_TypedLiteral():
    type1 = IRI("http://example.com/type1")
    type2 = IRI("http://example.com/type2")

    str1 = TypedLiteral("foo", type1)
    str2 = TypedLiteral("foo", type1)
    str3 = TypedLiteral("foo", type2)
    str4 = TypedLiteral("bar", type1)

    assert str1 == str2
    assert str1 != str3
    assert str1 != str4

    assert str3 > str1
    assert str1 < str3

    with pytest.raises(TypeError) as e:
        TypedLiteral(type1, type1)

    assert str(e.value) == "argument 1 must be str, not _hexastore.IRI"

    with pytest.raises(TypeError) as e:
        TypedLiteral("foo", "foo")

    assert str(e.value) == "argument 2 must be _hexastore.IRI, not str"


@pytest.mark.extension
def test_Variable():
    TITLE = Variable("a")

    assert repr(TITLE) == "Variable(value='a')"
    assert str(TITLE) == "a"
    assert bytes(TITLE) == b"a"

    assert TITLE == Variable("a")
    assert TITLE != "a"

    assert hash(TITLE)

    assert TITLE.value == "a"
