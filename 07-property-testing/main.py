"""Module 07: property-based testing - let Hypothesis try to break the patch generator.

Run:  python main.py
Hand-written examples test what you thought of. A property ("applying make_patch(a, b)
to a gives b, for ANY a and b") tests what you did not.
"""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


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


patching = load("04-json-patch")

# ---- 1. generate documents ---------------------------------------------------------

KEYS = st.sampled_from(["a", "b", "id", "x/y", "~", ""])
SCALARS = st.one_of(
    st.none(), st.booleans(), st.integers(-(10**20), 10**20),
    st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=4),
)
KEYED = st.lists(
    st.tuples(st.integers(0, 6), st.dictionaries(st.sampled_from(["a", "b"]), SCALARS, max_size=2)),
    max_size=5, unique_by=lambda t: t[0],
).map(lambda ts: [{**d, "id": i} for i, d in ts])
DOCS = st.recursive(
    SCALARS,
    lambda c: st.one_of(st.lists(c, max_size=4), st.dictionaries(KEYS, c, max_size=4), KEYED),
    max_leaves=12,
)


# ---- 2. make b a mutation of a, otherwise a and b share almost nothing ----------------


@st.composite
def mutate(draw: Any, v: Any) -> Any:
    if draw(st.integers(0, 9)) < 2:
        return copy.deepcopy(v)
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            act = 1 if k == "id" else draw(st.integers(0, 4))  # ids keep list items matchable
            if act:
                out[k] = draw(mutate(x)) if act >= 2 else copy.deepcopy(x)
        for _ in range(draw(st.integers(0, 2))):
            k = draw(KEYS)
            if k != "id":
                out[k] = draw(DOCS)
        return out
    if isinstance(v, list):
        items = [draw(mutate(x)) for x in v if draw(st.integers(0, 5))]
        if draw(st.booleans()):
            items = draw(st.permutations(items))
        for _ in range(draw(st.integers(0, 2))):
            items.insert(draw(st.integers(0, len(items))), draw(DOCS))
        return items
    return draw(DOCS)


PAIRS = DOCS.flatmap(lambda a: st.tuples(st.just(a), mutate(a)))
CONFIG = settings(max_examples=1000, deadline=None, database=None, suppress_health_check=list(HealthCheck))


# ---- 3. the property -------------------------------------------------------------------


@CONFIG
@given(PAIRS)
def round_trip(pair: tuple[Any, Any]) -> None:
    a, b = pair
    before = copy.deepcopy(a)
    patch = patching.make_patch(a, b)
    assert patching.same(patching.apply_patch(a, patch), b), (a, b, patch)
    assert a == before, "make_patch/apply_patch must not mutate their input"


# ---- 4. a deliberately broken generator: does the property notice? ---------------------


def buggy_list_patch(a: list[Any], b: list[Any]) -> list[dict[str, Any]]:
    """Index-mode list patch with the classic bug: removals in ASCENDING order."""
    n = min(len(a), len(b))
    ops: list[dict[str, Any]] = [{"op": "remove", "path": f"/{i}"} for i in range(n, len(a))]  # BUG
    ops += [{"op": "add", "path": f"/{j}", "value": b[j]} for j in range(len(a), len(b))]
    return ops


@settings(max_examples=500, deadline=None, database=None, suppress_health_check=list(HealthCheck))
@given(st.lists(st.integers(0, 3), max_size=6), st.lists(st.integers(0, 3), max_size=3))
def buggy_round_trip(a: list[int], b: list[int]) -> None:
    patched = patching.apply_patch(a, buggy_list_patch(a, b))
    # the buggy generator never edits the surviving prefix, so compare only the length
    assert len(patched) == len(b), (a, b)


def main() -> None:
    round_trip()  # raises with a minimal counterexample if the property is ever false
    try:
        buggy_round_trip()
    except AssertionError:
        print("hypothesis found the planted bug, as it should")
    except IndexError:
        print("hypothesis found the planted bug (it crashed the applier), as it should")
    else:
        raise AssertionError("the planted bug survived - the property is too weak")
    print("module 07 OK")


if __name__ == "__main__":
    main()
