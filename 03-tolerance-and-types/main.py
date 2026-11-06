"""Module 03: what "equal" means - numeric tolerance, exact big ints, NaN, ignore globs.

Run:  python main.py
This module's `diff` is the one the MCP wrapper (module 06) serves.
"""

from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import re
import sys
from fractions import Fraction
from typing import Any


def load(dirname: str) -> Any:
    """Import another module's main.py by path (the directory names contain hyphens)."""
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
kind = m02.kind


def numeric_equal(x: float, y: float, abs_tol: float = 0.0, rel_tol: float = 0.0) -> bool:
    """Are two numbers equal, optionally within a tolerance?

    Three traps this avoids:
      * NaN != NaN in IEEE floats, but a config that has NaN before and after did not change.
      * math.isclose(10**400, ...) overflows: ints that big cannot become floats.
      * float(2**80 + 1) == float(2**80): converting a big int loses the difference.
    Fraction(x) is exact for both ints and floats, so the arithmetic below never rounds.
    """
    x_nan = isinstance(x, float) and math.isnan(x)
    y_nan = isinstance(y, float) and math.isnan(y)
    if x_nan or y_nan:
        return x_nan and y_nan
    if x == y:  # Python compares int and float exactly: 1 == 1.0, 2**80 != 2**80 + 1
        return True
    # math.isinf(10**400) would itself overflow, so only ask floats.
    if (isinstance(x, float) and math.isinf(x)) or (isinstance(y, float) and math.isinf(y)):
        return False  # an infinity is only equal to itself (handled above)
    if not abs_tol and not rel_tol:
        return False
    fx, fy = Fraction(x), Fraction(y)
    delta = abs(fx - fy)
    return delta <= Fraction(abs_tol) or delta <= Fraction(rel_tol) * max(abs(fx), abs(fy))


def ignore_regexes(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    """'$.items[*].etag' -> a regex where * matches any text (dots and brackets included)."""
    out = []
    for p in patterns:
        if not p.startswith(("$", "*")):
            raise ValueError(f"ignore pattern {p!r} must start with '$' or '*'")
        out.append(re.compile("^" + ".*".join(re.escape(s) for s in p.split("*")) + "$"))
    return out


def diff(
    a: Any,
    b: Any,
    mode: str = "auto",
    abs_tol: float = 0.0,
    rel_tol: float = 0.0,
    ignore: tuple[str, ...] = (),
) -> list[tuple[Any, ...]]:
    rx = ignore_regexes(ignore)
    out: list[tuple[Any, ...]] = []

    def skip(path: str) -> bool:
        return any(r.match(path) for r in rx)

    def walk(x: Any, y: Any, path: str) -> None:
        if skip(path):
            return
        kx, ky = kind(x), kind(y)
        if kx != ky:
            out.append(("type_changed", path, x, y))
        elif kx == "object":
            for k in x:
                if k not in y:
                    if not skip(f"{path}.{k}"):
                        out.append(("removed", f"{path}.{k}", x[k], None))
                else:
                    walk(x[k], y[k], f"{path}.{k}")
            for k in y:
                if k not in x and not skip(f"{path}.{k}"):
                    out.append(("added", f"{path}.{k}", None, y[k]))
        elif kx == "array":
            m = m02.match(x, y, mode)
            for i in m["removed"]:
                if not skip(path + m02.label(m, x[i], i)):
                    out.append(("removed", path + m02.label(m, x[i], i), x[i], None))
            for j in m["added"]:
                if not skip(path + m02.label(m, y[j], j)):
                    out.append(("added", path + m02.label(m, y[j], j), None, y[j]))
            for i, j in m["pairs"]:
                walk(x[i], y[j], path + m02.label(m, x[i], i))
            if m["key"]:
                ordered = sorted(m["pairs"])
                stay = m02.lis_members([j for _, j in ordered])
                for pos, (i, j) in enumerate(ordered):
                    if pos not in stay:
                        out.append(("moved", path + m02.label(m, x[i], i), i, j))
        elif kx == "number":
            if not numeric_equal(x, y, abs_tol, rel_tol):
                out.append(("changed", path, x, y))
        elif x != y:
            out.append(("changed", path, x, y))

    walk(a, b, "$")
    return out


def selftest() -> None:
    # The classic: 0.1 + 0.2 is not 0.3 in binary floating point.
    assert diff({"v": 0.1 + 0.2}, {"v": 0.3}) == [("changed", "$.v", 0.1 + 0.2, 0.3)]
    assert diff({"v": 0.1 + 0.2}, {"v": 0.3}, abs_tol=1e-9) == []
    # Relative tolerance scales with the magnitude: 1% of 100 is 1.
    assert diff({"v": 100.0}, {"v": 100.9}, rel_tol=0.01) == []
    assert diff({"v": 100.0}, {"v": 101.5}, rel_tol=0.01) != []

    # 1 and 1.0 are the same JSON number; 1 and "1" and true are not.
    assert diff({"v": 1}, {"v": 1.0}) == []
    assert diff({"v": 1}, {"v": "1"})[0][0] == "type_changed"
    assert diff({"v": 1}, {"v": True})[0][0] == "type_changed"

    # Big integers stay exact (a float would call these equal) ...
    big = 2**80
    assert diff({"v": big}, {"v": big + 1}) != []
    assert float(big) == float(big + 1)  # ... which is exactly the trap.
    # ... and even absurdly large ones do not overflow when a tolerance is set.
    assert numeric_equal(10**400, 10**400 + 1, rel_tol=1e-9)

    # NaN equals NaN, infinity only itself.
    nan, inf = float("nan"), float("inf")
    assert diff({"v": nan}, {"v": nan}) == []
    assert diff({"v": nan}, {"v": 0}) != []
    assert diff({"v": inf}, {"v": inf}) == []
    assert diff({"v": inf}, {"v": -inf}) != []

    # Ignore globs: noisy fields (timestamps, etags) hide the signal.
    a = {"meta": {"ts": 1}, "items": [{"id": 1, "etag": "x", "v": 1}], "ts": 5}
    b = {"meta": {"ts": 2}, "items": [{"id": 1, "etag": "y", "v": 2}], "ts": 6}
    assert [d[1] for d in diff(a, b)] == ["$.meta.ts", "$.items[id=1].etag", "$.items[id=1].v", "$.ts"]
    assert [d[1] for d in diff(a, b, ignore=("*.ts", "$.items[*].etag"))] == ["$.items[id=1].v"]
    try:
        diff(a, b, ignore=("ts",))
    except ValueError as e:
        assert "must start with" in str(e)
    else:
        raise AssertionError("an unanchored ignore pattern must be rejected")

    # Values survive a trip through JSON, which is how an agent will see them.
    json.dumps(diff({"v": 1}, {"v": 2}))
    print("module 03 OK")


if __name__ == "__main__":
    selftest()
