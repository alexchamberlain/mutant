from .ast import IRI, BlankNode


def serialise(store, fo, namespaces):
    serialiser = _Serialiser(store, namespaces)
    serialiser(fo)


class _Serialiser:
    def __init__(self, store, namespaces):
        self._store = store
        self._namespaces = namespaces
        self._terms = {
            t: self._serialise_term(t)
            for t in store.terms()
            if not isinstance(t, tuple) and not isinstance(t, BlankNode)
        }

    def __call__(self, fo):
        for n, i in self._namespaces:
            fo.write(f"@prefix {n}: <{i.value}> .\n")
        fo.write("\n")

        for s, po in self._store.spo.items():
            if isinstance(s, tuple) or isinstance(s, BlankNode):
                # Skip reified statements
                continue

            ps = [self._serialise_predicate_object_list(p, os) for p, os in po.items()]
            pss = " ;\n    ".join(ps)

            fo.write(f"{self._terms[s]} {pss} .\n\n")

    def _serialise_predicate_object_list(self, p, os):
        objs = [self._terms[o] for o, status in os.items() if status.inserted]
        o = ", ".join(objs)

        return f"{self._terms[p]} {o}"

    def _serialise_term(self, t):
        if isinstance(t, IRI):
            # TODO: Make this better
            for n, i in self._namespaces:
                if t.value.startswith(i.value):
                    return f"{n}:{t.value[len(i.value):]}"
            return f"<{t.value}>"
        elif isinstance(t, str):
            return f'"{t}"'
        else:
            import pdb

            pdb.set_trace()
            raise TypeError(f"Unknown type {type(t)} ({t})")
