from hexastore.ast import IRI, Variable, BlankNode, TripleStatus, TripleStatusItem
from hexastore.model import Solution, Key

import pytest

DAVE_SMITH = IRI("http://example.com/dave-smith")
ERIC_MILLER = IRI("http://example.com/eric-miller")
ERIC_MILLER_MBOX = IRI("mailto:e.miller123(at)example")

TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

KNOWS = IRI("http://xmlns.com/foaf/0.1/knows")
MBOX = IRI("http://xmlns.com/foaf/0.1/mbox")
NAME = IRI("http://xmlns.com/foaf/0.1/name")
PERSON = IRI("http://xmlns.com/foaf/0.1/Person")
TITLE = IRI("http://xmlns.com/foaf/0.1/title")


@pytest.mark.ast
def test_IRI():
    assert str(TITLE) == "http://xmlns.com/foaf/0.1/title"
    assert bytes(TITLE) == b"http://xmlns.com/foaf/0.1/title"

    assert Key(TITLE) < Key("http://xmlns.com/foaf/0.1/title")
    assert TITLE == IRI("http://xmlns.com/foaf/0.1/title")
    assert TITLE != "http://xmlns.com/foaf/0.1/title"
    assert Key(NAME) < Key(TITLE)

    with pytest.raises(TypeError):
        Key(TITLE) < Key({})

    assert Key(NAME) == Key(NAME)
    assert not (Key(NAME) < Key(NAME))
    assert not (Key(NAME) > Key(NAME))


@pytest.mark.ast
def test_Variable():
    assert str(Variable("x")) == "x"
    assert bytes(Variable("x")) == b"x"


@pytest.mark.ast
def test_BlankNode():
    node1 = BlankNode()
    node2 = BlankNode()

    assert node1 != node2

    assert str(node1)
    assert repr(node1)


@pytest.mark.ast
def test_TripleStatus():
    status = TripleStatus([])

    assert not status.inserted

    status.statuses.append(TripleStatusItem(valid_from=4))

    assert status.inserted

    status.statuses[0].valid_to = 5

    assert not status.inserted


@pytest.mark.ast
def test_Solution():
    assert Solution(
        {Variable("s"): ERIC_MILLER, Variable("p"): KNOWS, Variable("o"): DAVE_SMITH},
        [],
        {(ERIC_MILLER, KNOWS, DAVE_SMITH)},
    ) == Solution(
        {Variable("s"): ERIC_MILLER, Variable("p"): KNOWS, Variable("o"): DAVE_SMITH},
        [],
        {(ERIC_MILLER, KNOWS, DAVE_SMITH)},
    )

    assert (
        repr(Solution({Variable("s"): ERIC_MILLER}, [], {(ERIC_MILLER, KNOWS, DAVE_SMITH)}))
        == "Solution({Variable(value='s'): IRI(value='http://example.com/eric-miller')}, ..., {(IRI(value='http://example.com/eric-miller'), IRI(value='http://xmlns.com/foaf/0.1/knows'), IRI(value='http://example.com/dave-smith'))})"
    )


@pytest.mark.ast
def test_Solution_lt():
    assert Solution(
        {Variable("s"): ERIC_MILLER, Variable("p"): KNOWS, Variable("o"): DAVE_SMITH},
        [],
        {(ERIC_MILLER, KNOWS, DAVE_SMITH)},
    ) < Solution(
        {Variable("s"): DAVE_SMITH, Variable("p"): TYPE, Variable("o"): PERSON}, [], {(ERIC_MILLER, KNOWS, DAVE_SMITH)}
    )
