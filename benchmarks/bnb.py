import logging
import sys
import time

from rdflib.graph import Graph

from hexastore import turtle
from hexastore.memory import InMemoryHexastore

logger = logging.getLogger(__name__)


root = logging.getLogger()
root.setLevel(logging.DEBUG)


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end = time.perf_counter()
        self.interval = self.end - self.start


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)

try:
    with Timer() as t:
        store = InMemoryHexastore()

        with Timer() as t1:
            triples = []
            with open("/Users/alex/Downloads/BNBLODBooks_sample_nt/BNBLODB_sample.nt") as fo:
                turtle.parse(fo.read(), lambda s, p, o: triples.append((s, p, o)))

        logger.info(f"library=mutant-parse time={t1.interval}")

        with Timer() as t2:
            store.bulk_insert(triples)

        logger.info(f"library=mutant-bulk-insert time={t2.interval}")
finally:
    logger.info(f"library=mutant time={t.interval}")

try:
    with Timer() as t:
        g = Graph()
        g.parse("/Users/alex/Downloads/BNBLODBooks_sample_nt/BNBLODB_sample.nt", format="nt")
finally:
    logger.info(f"library=rdflib time={t.interval}")
