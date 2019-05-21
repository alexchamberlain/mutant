# Mutant

A forward reasoning logic language for RDF.

## Example

Let us suppose we have the following Turtle file:

```
@prefix schema: <https://schema.org/> .
@prefix example: <https://example.org/> .

example:pebbles schema:name "Pebbles Flintstone" .
example:bamn-bamn schema:name "Bamm-Bamm Rubble" .
example:roxy schema:name "Roxy Rubble" ;
    schema:parent example:pebbles, example:bamn-bamn .
example:chip schema:name "Chip Rubble" ;
    schema:parent example:pebbles, example:bamn-bamn .
```

It's fair to say that based on the above information, Roxy is a sibling of Chip, and vice versa. We can encode that in `mutant` using the following code

```
@prefix schema: <https://schema.org/> .

($child1 schema:parent $parent), ($child2 schema:parent $parent) st ($child1 is-not $child2)
    → ($child1 schema:sibling $child2) .
```

You can run this by using the following command:

    python mutant.py reason -n example https://example.org/ -n schema https://schema.org/ examples/family-tree-simple/rules.mtt examples/family-tree-simple/base.ttl -

Which will produce the following output:

```
@prefix example: <https://example.org/> .
@prefix schema: <https://schema.org/> .

example:bamn-bamn schema:name "Bamm-Bamm Rubble" .

example:chip schema:name "Chip Rubble" ;
    schema:parent example:bamn-bamn, example:pebbles ;
    schema:sibling example:roxy .

example:pebbles schema:name "Pebbles Flintstone" .

example:roxy schema:name "Roxy Rubble" ;
    schema:parent example:bamn-bamn, example:pebbles ;
    schema:sibling example:chip .
```

A more complex example with symmetric and inverse properties (`schema:spouse` and `schema:children`) is provided in `examples/family-tree`.

## Technology

`mutant` is implemented as a single Python package `hexastore`, which has the following levelised structure:

1. `ast`, `bisect`
2. `typing`, `wal`, `turtle_serialiser`, `namespace`
3. `model`, `turtle`, `sorted`
4. `util`, `memory`, `engine`, `forward_reasoner`
5. `memorywal`, `generic_rule`

`mutant` is a proof of concept, and therefore, the modules aren't necessarily complete or completely coherant. For example, `memory` has support for blank nodes and reified statements, but the turtle serialiser would break miserably if you gave it a blank node.

### `memory`: In Memory Hexastore

`hexastore.memory` implements an in-memory hexastore, based on a paper entitled [Hexastore: Sextuple Indexing for Semantic Web Data Management][1]. It heavily relies on the `sorted` module, which implements a sorted list, sorted mapping and a default variant thereof. This makes the hexastore implement quite simple and succinct. The hexastore structure has been extended to support reified statements, versioned history and inserted/deleted statements.

### `engine`: Pattern matching engine

`hexastore.engine` implements a basic pattern matching engine over the hexastore interface. It's vaguely based on Basic Graph Patterns from SPARQL, as it was original intended to be developed into a SPARQL engine, but it's not very close to that yet.

### `forward_reasoner`: A semi-naive forward reasoner

`hexastore.forward_reasoner` implements a semi-naive forward reasoner for RDF, based on ideas from [Datalog][2]. "semi-naive" simply means that during rule iteration, you only consider triples that have been added in the previous iteration. The forward reasoner records how a triple was found, which allows us to delete triples efficiently.

#### Limitations/TODO/Caveats/Warnings

1. [ ] Remove rule implementations and replace them by `mutant` language coded rules.
2. [ ] Rules need to be loaded _before_ the triples at the moment to work; this isn't good enough for a realistic system.

### `generic_rule`: `mutant` language parser

The forward reasoner ~~doesn't~~ shouldn't know anything about particular rules; it just implements the forward reasoning engine. The rules themselves are written in a DSL, which simplifies understanding them considerably. `hexastore.generic_rule` implements the parser and adapts the AST into an executable rule for the forward reasoner.

### `turtle`/`turtle_serialiser`: Basic parser/serialiser for turtle

We need to read and write from some format; Turtle is both readable and simple enough to write a parser in a couple of hours. The parser and serialiser are good enough for the examples in the repo; in particular, blank node support is not complete.

## Why Python?

To get out ahead of this one, Python was used simply because it's the language I'm most comfortable with and productive in. In this PoC, I wanted to concentrate on the datastructures in use, rather than top notch performance. It also has some amazing patterns, such as the Sequence and Mapping Protocols, that make implementing a Hexastore quite elegant.

[1]: http://www.vldb.org/pvldb/1/1453965.pdf
[2]: https://en.wikipedia.org/wiki/Datalog