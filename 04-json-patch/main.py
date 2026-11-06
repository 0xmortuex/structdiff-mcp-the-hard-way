"""Module 04: generate an RFC 6902 JSON Patch, and apply one to prove it works.

Run:  python main.py
"""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import random
import sys
from typing import Any


def load(dirname: str) -> Any:
    path = pathlib.Path(__file__).resolve().parent.parent / dirname / "main.py"
    name = "m_" + dirname.replace("-", "_")
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


m02 = load("02-list-matching")
m03 = load("03-tolerance-and-types")
kind = m02.kind


def ptr(tokens: list[Any]) -> str:
    """JSON Pointer. '~' must be escaped before '/', or '~1' would be double-decoded."""
    return "".join("/" + str(t).replace("~", "~0").replace("/", "~1") for t in tokens)


# ------------------------------------------------------------------ generating


def make_patch(a: Any, b: Any, mode: str = "auto", at: list[Any] | None = None) -> list[dict[str, Any]]:
    at = at or []
    ka, kb = kind(a), kind(b)
    if ka != kb:
        return [{"op": "replace", "path": ptr(at), "value": copy.deepcopy(b)}]
    if ka == "object":
        ops = [{"op": "remove", "path": ptr([*at, k])} for k in a if k not in b]
        for k in b:
            if k in a:
                ops += make_patch(a[k], b[k], mode, [*at, k])
            else:
                ops.append({"op": "add", "path": ptr([*at, k]), "value": copy.deepcopy(b[k])})
        return ops
    if ka == "array":
        return _list_patch(a, b, mode, at)
    if ka == "number":
        same = m03.numeric_equal(a, b)
    else:
        same = a == b
    return [] if same else [{"op": "replace", "path": ptr(at), "value": copy.deepcopy(b)}]


def _list_patch(a: list[Any], b: list[Any], mode: str, at: list[Any]) -> list[dict[str, Any]]:
    m = m02.match(a, b, mode)
    ops: list[dict[str, Any]] = []

    # 1. Remove, highest index first: removing index 1 shifts everything after it down,
    #    so ascending order would delete the wrong items.
    for i in sorted(m["removed"], reverse=True):
        ops.append({"op": "remove", "path": ptr([*at, i])})

    # 2. Walk b left to right keeping `cur`, a simulation of the list after each op.
    #    Invariant: cur[:j] already equals the first j items of the target order.
    gone = set(m["removed"])
    cur = [("a", i) for i in range(len(a)) if i not in gone]
    a_of_b = {j: i for i, j in m["pairs"]}
    for j in range(len(b)):
        if j in a_of_b:
            tok = ("a", a_of_b[j])
            p = cur.index(tok)  # always >= j, because cur[:j] is finished
            if p != j:
                ops.append({"op": "move", "from": ptr([*at, p]), "path": ptr([*at, j])})
                cur.pop(p)
                cur.insert(j, tok)
        else:
            ops.append({"op": "add", "path": ptr([*at, j]), "value": copy.deepcopy(b[j])})
            cur.insert(j, ("new", j))

    # 3. Now every matched item sits at its final index j, so edits inside it can use it.
    for i, j in m["pairs"]:
        ops += make_patch(a[i], b[j], mode, [*at, j])
    return ops


# ------------------------------------------------------------------ applying


def _split(p: str) -> list[str]:
    if p == "":
        return []
    assert p.startswith("/"), f"bad pointer {p!r}"
    return [t.replace("~1", "/").replace("~0", "~") for t in p[1:].split("/")]


def _parent(doc: Any, tokens: list[str]) -> Any:
    for t in tokens:
        doc = doc[t] if isinstance(doc, dict) else doc[int(t)]
    return doc


def _add(doc: Any, path: str, value: Any) -> Any:
    toks = _split(path)
    if not toks:
        return value
    parent, last = _parent(doc, toks[:-1]), toks[-1]
    if isinstance(parent, dict):
        parent[last] = value
    else:
        parent.insert(len(parent) if last == "-" else int(last), value)
    return doc


def _remove(doc: Any, path: str) -> tuple[Any, Any]:
    toks = _split(path)
    parent, last = _parent(doc, toks[:-1]), toks[-1]
    return doc, parent.pop(last) if isinstance(parent, dict) else parent.pop(int(last))


def apply_patch(doc: Any, patch: list[dict[str, Any]]) -> Any:
    """Apply add / remove / replace / move to a COPY of doc."""
    doc = copy.deepcopy(doc)
    for op in patch:
        name, path = op["op"], op["path"]
        if name == "add":
            doc = _add(doc, path, copy.deepcopy(op["value"]))
        elif name == "remove":
            doc, _ = _remove(doc, path)
        elif name == "replace":
            if not _split(path):
                doc = copy.deepcopy(op["value"])
            else:
                doc, _ = _remove(doc, path)  # replace = remove + add at the same place
                doc = _add(doc, path, copy.deepcopy(op["value"]))
        elif name == "move":
            doc, value = _remove(doc, op["from"])
            doc = _add(doc, path, value)  # the target index is read AFTER the removal
        else:
            raise ValueError(f"unsupported op {name!r}")
    return doc


def same(a: Any, b: Any) -> bool:
    """Deep equality that, unlike ==, knows True is not 1."""
    if kind(a) != kind(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return bool(m03.numeric_equal(a, b)) if kind(a) == "number" else bool(a == b)


def selftest() -> None:
    # Readable output for a reorder: one move, not a delete-and-recreate.
    a = [{"id": 1}, {"id": 2}, {"id": 3}]
    b = [{"id": 3}, {"id": 1}, {"id": 2}]
    assert make_patch(a, b) == [{"op": "move", "from": "/2", "path": "/0"}]

    # Pointer escaping: a key named "a/b" and one named "~".
    p = make_patch({"a/b": {"~": 1}}, {"a/b": {"~": 2}})
    assert p == [{"op": "replace", "path": "/a~1b/~0", "value": 2}]

    # Removal order matters.
    assert make_patch([1, 2, 3, 4], [1, 4], mode="index") == [
        {"op": "remove", "path": "/3"},
        {"op": "remove", "path": "/2"},
        {"op": "replace", "path": "/1", "value": 4},
    ]

    # The root can be replaced.
    assert make_patch([1], {"a": 1}) == [{"op": "replace", "path": "", "value": {"a": 1}}]

    # The only test that matters: applying the patch to a really produces b.
    a = {"users": [{"id": 1, "r": "x"}, {"id": 2}, {"id": 3}], "gone": 1, "n": [1, 2]}
    b = {"users": [{"id": 3}, {"id": 1, "r": "y"}, {"id": 4}], "new": {"k": [True]}, "n": [1, 2, 3]}
    assert same(apply_patch(a, make_patch(a, b)), b)
    assert a["gone"] == 1, "apply_patch must not modify its input"

    # A small randomized check; module 07 does this properly with Hypothesis.
    rng = random.Random(7)

    def rand(depth: int = 0) -> Any:
        r = rng.random()
        if depth > 2 or r < 0.3:
            return rng.choice([None, True, False, 0, 1, 2.5, "a", "b"])
        if r < 0.65:
            return [rand(depth + 1) for _ in range(rng.randint(0, 4))]
        return {rng.choice("abc"): rand(depth + 1) for _ in range(rng.randint(0, 3))}

    for _ in range(500):
        x, y = rand(), rand()
        assert same(apply_patch(x, make_patch(x, y)), y), (x, y)
    print("module 04 OK")


if __name__ == "__main__":
    selftest()
