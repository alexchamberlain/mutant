import pytest

from hexastore.ast import IRI, Variable
from hexastore.model import Key, Solution

A = IRI("http://example.com/A")
B = IRI("http://example.com/B")
C = IRI("http://example.com/C")
D = IRI("http://example.com/D")


@pytest.mark.model
def test_Key():
    keyA = Key(A)
    keyAp = Key(A)
    keyB = Key(B)
    key42 = Key(42)

    assert keyA == keyAp
    assert keyA != keyB
    assert keyA != key42


@pytest.mark.model
def test_Solution():
    s = Solution({Variable("A"): A}, [], set())

    assert s.copy() is not s
    assert s.copy() == s

    sp = s.copy()
    sp.update({Variable("B"): B})

    assert s != sp
    assert sp.get(Variable("B")) == B
