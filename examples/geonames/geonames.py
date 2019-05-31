import decimal
import csv

from hexastore.memory import InMemoryHexastore
from hexastore.ast import IRI
from hexastore.turtle_serialiser import serialise

CONFIG = [
    ("geonameid", None, None),
    ("name", IRI("http://www.geonames.org/ontology#name"), None),
    ("asciiname", None, None),
    ("alternatenames", None, None),  # altenativenames removed by choice
    ("latitude", IRI("http://www.w3.org/2003/01/geo/wgs84_pos#lat"), decimal.Decimal),
    ("longitude", IRI("http://www.w3.org/2003/01/geo/wgs84_pos#long"), decimal.Decimal),
    (
        "feature class",
        IRI("http://www.geonames.org/ontology#featureClass"),
        lambda x: IRI(f"http://www.geonames.org/ontology#{x}"),
    ),
    ("feature code", IRI("http://www.geonames.org/ontology#featureCode"), None),
    ("country code", IRI("http://www.geonames.org/ontology#countryCode"), None),
    ("cc2", None, None),
    ("admin1 code", IRI("http://www.geonames.org/ontology#parentADM1"), None),
    ("admin2 code", IRI("http://www.geonames.org/ontology#parentADM2"), None),
    ("admin3 code", IRI("http://www.geonames.org/ontology#parentADM3"), None),
    ("admin4 code", IRI("http://www.geonames.org/ontology#parentADM4"), None),
    ("population", IRI("http://www.geonames.org/ontology#population"), int),
    ("elevation", None, None),  #  TODO: Not sure what this should be mapped to
    ("dem", None, None),
    ("timezone", None, None),  #  TODO: Not sure what this should be mapped to
    ("modification date", None, None),
]

store = InMemoryHexastore()

"""
xmlns:cc="http://creativecommons.org/ns#"
xmlns:dcterms="http://purl.org/dc/terms/"
xmlns:foaf="http://xmlns.com/foaf/0.1/"
xmlns:gn="http://www.geonames.org/ontology#"
xmlns:owl="http://www.w3.org/2002/07/owl#"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
xmlns:wgs84_pos="http://www.w3.org/2003/01/geo/wgs84_pos#">

<gn:population>7556900</gn:population>
<wgs84_pos:lat>51.50853</wgs84_pos:lat>
<wgs84_pos:long>-0.12574</wgs84_pos:long>
"""

TYPE = IRI("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
FEATURE = IRI("http://www.geonames.org/ontology#Feature")

# with open("/Users/alex/Downloads/allCountries.txt", "r") as fo:
with open("london.txt", "r") as fo:
    # with open("/Users/alex/Downloads/GB/GB.txt", "r") as fo:
    reader = csv.reader(fo, delimiter="\t")
    for row in reader:
        iri = IRI(f"http://sws.geonames.org/{row[0]}/")

        store.insert(iri, TYPE, FEATURE, 0)

        for config, cell in zip(CONFIG, row):
            if config[1] is not None and cell:
                if config[2]:
                    cell = config[2](cell)
                store.insert(iri, config[1], cell, 0)

print(f"len(store) = {len(store)}")

with open("out.ttl", "w") as fo:
    serialise(
        store,
        fo,
        [
            ("geonames", IRI("http://www.geonames.org/ontology#")),
            ("geo", IRI("http://www.w3.org/2003/01/geo/wgs84_pos#")),
        ],
    )
