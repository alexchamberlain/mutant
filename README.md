# Cerberus

A PoC Deductive Triple Store, with an aim to be a Distributed Deductive Rewindable Triple Store.

## What is a Distributed Deductive Rewindable Triple Store?

* **Triple Store** A triple store is a very interesting model for data storage, contraposing RDBMS, column stores, object stores, document stores etc. It models data based on 3 terms: subject-predicate-object. "Alex a Person", "Alex worksFor Bloomberg" etc. It can be seen as a storage form of RDF, though it need not be limited to RDF. Furthermore, it can easily be extended with triples referencing other triples for various use cases. The storage modules are based on a paper proposing a bespoke storage format for Triple Stores called [Hexastore: Sextuple Indexing for Semantic Web Data Management][1].
* **Distributed** Most modern data solutions are being built distributed from the ground up - examples include ZooKeeper, CockroachDB, Cassandra etc. As far as I can tell, there are very few options in this space for Triple Stores, and where there are, they are either tacked onto the side or a commercial solution. This PoC is _not_ distributed, but does include a Write-Ahead Log integral to its design, so it should be feasible to extend this to a distributed system via the Raft Protocol or similar.
* **Deductive** Given the simple nature of triple stores, there have been several attempts at mapping datalog to the format, which allows you to deduce triples based on other triples. For example, "Alex worksFor Bloomberg" implies that "Alex a Person" and "Bloomberg a Organisation" (based on the [`domain`][2] and [`range`][3] of the predicate [`worksFor`][4]). In general, these are called Reasoners, and vary from very simple and inflexible to the utterly complex and theoretical. We're aiming for a compromise in the middle based on a semi-naiive forward reasoning algorithm, based loosely on reading about how Datalog systems are implemented.
* **Rewindable** It's relatively easy to track which version added a triple and which version removed it. Assuming that this information is never removed, it is possible to "rewind" history within the database and understand what it looked like at any previous version. If the timestamp of each version is then tracked, it is also possible to rewind history to any point in time too. In this PoC, that is the limit of the implementation, but it is envisaged that tools to merge versions, simplify history, remove subjects completely from history etc could be developed to answer different use cases.

## Why Python?

To get out ahead of this one, Python was used simply because it's the language I'm most comfortable with and productive in. In this PoC, I wanted to concentrate on the datastructures in use, rather than top notch performance. That being said, in informal benchmarks, using PyPy with various stages of prototype did produce some very impressive results. It also has some amazing patterns, such as the Sequence and Mapping Protocols, that make implementing a Hexastore quite elegant.

## Alternatives

This is no where near ready to store real data for long periods of time, and there are several OSS and commercial solutions available, with different trade offs.

* [AWS Neptune][5]
* [Blazegraph][6]
* [Marmotta][7]
* [OpenLink Virtuoso][8]

There are also a fair number of Graph Databases in this space, including Neo4J and dgraph.


[1]: http://www.vldb.org/pvldb/1/1453965.pdf
[2]: https://www.w3.org/TR/rdf-schema/#ch_domain
[3]: https://www.w3.org/TR/rdf-schema/#ch_range
[4]: https://schema.org/worksFor
[5]: https://aws.amazon.com/neptune/
[6]: https://www.blazegraph.com/
[7]: http://marmotta.apache.org/
[8]: https://virtuoso.openlinksw.com/