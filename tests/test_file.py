import os
import tempfile

import pytest

from hexastore import IRI, BlankNodeFactory, InMemoryHexastore
from hexastore.disk import Builder, FileHandler
from hexastore.turtle import parse

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
def test_full_circle():
    path = from_file_to_tmp(os.path.join(dir_path, "data/eric.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    spo = {
        IRI("http://www.w3.org/People/EM/contact#me"): {
            IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"): [
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Person")
            ],
            IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"): ["Eric Miller"],
            IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox"): [IRI("mailto:e.miller123(at)example")],
            IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle"): ["Dr."],
        },
        IRI("https://alexchamberlain.co.uk/#me"): {
            IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"): [
                IRI("http://www.w3.org/2000/10/swap/pim/contact#Person")
            ],
            IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"): ["Alex Chamberlain"],
            IRI("https://schema.org/name"): ["Alex Chamberlain"],
        },
    }
    pos = {
        IRI("https://schema.org/name"): {"Alex Chamberlain": [IRI("https://alexchamberlain.co.uk/#me")]},
        IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"): {
            IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"): [
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("https://alexchamberlain.co.uk/#me"),
            ]
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"): {
            "Alex Chamberlain": [IRI("https://alexchamberlain.co.uk/#me")],
            "Eric Miller": [IRI("http://www.w3.org/People/EM/contact#me")],
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox"): {
            IRI("mailto:e.miller123(at)example"): [IRI("http://www.w3.org/People/EM/contact#me")]
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle"): {
            "Dr.": [IRI("http://www.w3.org/People/EM/contact#me")]
        },
    }
    osp = {
        "Alex Chamberlain": {
            IRI("https://alexchamberlain.co.uk/#me"): [
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                IRI("https://schema.org/name"),
            ]
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"): {
            IRI("http://www.w3.org/People/EM/contact#me"): [IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")],
            IRI("https://alexchamberlain.co.uk/#me"): [IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")],
        },
        "Eric Miller": {
            IRI("http://www.w3.org/People/EM/contact#me"): [IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName")]
        },
        IRI("mailto:e.miller123(at)example"): {
            IRI("http://www.w3.org/People/EM/contact#me"): [IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox")]
        },
        "Dr.": {
            IRI("http://www.w3.org/People/EM/contact#me"): [
                IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle")
            ]
        },
    }
    sop = {
        IRI("https://alexchamberlain.co.uk/#me"): {
            "Alex Chamberlain": [
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                IRI("https://schema.org/name"),
            ],
            IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"): [
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
            ],
        },
        IRI("http://www.w3.org/People/EM/contact#me"): {
            IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"): [
                IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
            ],
            "Eric Miller": [IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName")],
            IRI("mailto:e.miller123(at)example"): [IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox")],
            "Dr.": [IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle")],
        },
    }
    ops = {
        "Alex Chamberlain": {
            IRI("https://schema.org/name"): [IRI("https://alexchamberlain.co.uk/#me")],
            IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"): [IRI("https://alexchamberlain.co.uk/#me")],
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#Person"): {
            IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"): [
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("https://alexchamberlain.co.uk/#me"),
            ]
        },
        "Eric Miller": {
            IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"): [IRI("http://www.w3.org/People/EM/contact#me")]
        },
        IRI("mailto:e.miller123(at)example"): {
            IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox"): [IRI("http://www.w3.org/People/EM/contact#me")]
        },
        "Dr.": {
            IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle"): [
                IRI("http://www.w3.org/People/EM/contact#me")
            ]
        },
    }
    pso = {
        IRI("https://schema.org/name"): {IRI("https://alexchamberlain.co.uk/#me"): ["Alex Chamberlain"]},
        IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"): {
            IRI("http://www.w3.org/People/EM/contact#me"): [IRI("http://www.w3.org/2000/10/swap/pim/contact#Person")],
            IRI("https://alexchamberlain.co.uk/#me"): [IRI("http://www.w3.org/2000/10/swap/pim/contact#Person")],
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"): {
            IRI("http://www.w3.org/People/EM/contact#me"): ["Eric Miller"],
            IRI("https://alexchamberlain.co.uk/#me"): ["Alex Chamberlain"],
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox"): {
            IRI("http://www.w3.org/People/EM/contact#me"): [IRI("mailto:e.miller123(at)example")]
        },
        IRI("http://www.w3.org/2000/10/swap/pim/contact#personalTitle"): {
            IRI("http://www.w3.org/People/EM/contact#me"): ["Dr."]
        },
    }

    assert handler.spo == spo
    assert handler.pos == pos
    assert handler.osp == osp
    assert handler.sop == sop
    assert handler.ops == ops
    assert handler.pso == pso

    assert handler.spo[IRI("http://www.w3.org/People/EM/contact#me")][
        IRI("http://www.w3.org/2000/10/swap/pim/contact#mailbox")
    ] == [IRI("mailto:e.miller123(at)example")]

    _manual_equality(handler.spo, spo)
    _manual_equality(handler.pos, pos)
    _manual_equality(handler.osp, osp)
    _manual_equality(handler.sop, sop)
    _manual_equality(handler.ops, ops)
    _manual_equality(handler.pso, pso)

    assert (
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                "Eric Miller",
            ) in handler
    assert (
        handler.index(
            (
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                "Eric Miller",
            )
        )
        == 1
    )
    
    assert (
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                "Alex Chamberlain",
            ) not in handler
    assert (
        handler.index(
            (
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                "Alex Chamberlain",
            )
        )
        is None
    )

    assert (
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                "Foobar",
            ) not in handler
    assert (
        handler.index(
            (
                IRI("http://www.w3.org/People/EM/contact#me"),
                IRI("http://www.w3.org/2000/10/swap/pim/contact#fullName"),
                "Foobar",
            )
        )
        is None
    )

    assert list(handler.triples()) == list(_flatten(spo))


@pytest.mark.disk
def test_full_circle_with_blank_nodes():
    path = from_file_to_tmp(os.path.join(dir_path, "data/alex_with_blank_nodes.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    laura_node = next(iter(handler.spo[IRI("https://alexchamberlain.co.uk/#me")][IRI("https://schema.org/spouse")]))

    assert handler.spo[laura_node][IRI("https://schema.org/name")] == ["Laura Chamberlain"]


@pytest.mark.disk
def test_full_circle_with_reification():
    path = from_file_to_tmp(os.path.join(dir_path, "data/alex_with_reification.ttl"))

    blank_node_factory = BlankNodeFactory()
    handler = FileHandler(path, blank_node_factory)

    assert handler.spo[
        (
            IRI("https://alexchamberlain.co.uk/#me"),
            IRI("https://schema.org/spouse"),
            IRI("https://alexchamberlain.co.uk/#laura"),
        )
    ][IRI("https://alexchamberlain.co.uk/#interviewWith")] == [IRI("https://alexchamberlain.co.uk/#me")]


def _manual_equality(file_index, dict_index):
    for s, po in dict_index.items():
        for p, o in po.items():
            assert file_index[s][p] == o


def _flatten(index):
    for s, po in index.items():
        for p, o_s in po.items():
            for o in o_s:
                yield (s, p, o)
