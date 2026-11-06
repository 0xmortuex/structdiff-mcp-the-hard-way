"""Module 01: a semantic diff by walking two trees.

Run:  python main.py
Output is a list of (op, path, old, new) tuples. The self-test at the bottom is the
specification: if README.md and this file ever disagree, the assertions win.
"""

from __future__ import annotations

from typing import Any


def kind(v: Any) -> str:
    """The JSON type of a value. bool must be tested before int: True is an int in Python,
    but `{"debug": true}` becoming `{"debug": 1}` is a real change."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, dict):
        return "object"
    if isinstance(v, list):
        return "array"
    raise TypeError(f"not JSON data: {type(v).__name__}")


def diff(a: Any, b: Any, path: str = "$") -> list[tuple[str, str, Any, Any]]:
    """Return (op, path, old, new) for everything that differs between a and b.

    op is one of: added, removed, changed, type_changed. `old`/`new` are None when they
    do not apply (an added key has no old value) - the op tells you which one to trust.
    """
    ka, kb = kind(a), kind(b)
    if ka != kb:
        # 1 -> "1" is not "a changed number": the type itself changed. Say so.
        return [("type_changed", path, a, b)]
    if ka == "object":
        out = []
        for key in a:  # keys of a: removed, or compare the values
            child = f"{path}.{key}"
            if key not in b:
                out.append(("removed", child, a[key], None))
            else:
                out += diff(a[key], b[key], child)
        for key in b:
            if key not in a:
                out.append(("added", f"{path}.{key}", None, b[key]))
        return out
    if ka == "array":
        # Naive on purpose: items are paired by position. Module 02 fixes this.
        out = []
        for i in range(min(len(a), len(b))):
            out += diff(a[i], b[i], f"{path}[{i}]")
        for i in range(len(b), len(a)):
            out.append(("removed", f"{path}[{i}]", a[i], None))
        for i in range(len(a), len(b)):
            out.append(("added", f"{path}[{i}]", None, b[i]))
        return out
    if a != b:
        return [("changed", path, a, b)]
    return []


def selftest() -> None:
    # Key order never matters: that is what makes this better than a line diff.
    assert diff({"a": 1, "b": [1, 2]}, {"b": [1, 2], "a": 1}) == []

    # Added / removed / changed, with paths you can read.
    old = {"name": "api", "port": 8080, "tls": {"enabled": False, "cert": "a.pem"}}
    new = {"name": "api", "port": 9090, "tls": {"enabled": True}, "workers": 4}
    assert diff(old, new) == [
        ("changed", "$.port", 8080, 9090),
        ("changed", "$.tls.enabled", False, True),
        ("removed", "$.tls.cert", "a.pem", None),
        ("added", "$.workers", None, 4),
    ]

    # Type changes are their own thing, and bool is not int.
    assert diff({"v": 1}, {"v": "1"}) == [("type_changed", "$.v", 1, "1")]
    assert diff({"v": True}, {"v": 1}) == [("type_changed", "$.v", True, 1)]

    # null is a value; a missing key is not.
    assert diff({"a": None}, {}) == [("removed", "$.a", None, None)]
    assert diff({"a": None}, {"a": None}) == []

    # Lists are compared by position (for now).
    assert diff([1, 2, 3], [1, 5]) == [("changed", "$[1]", 2, 5), ("removed", "$[2]", 3, None)]

    # Unicode is just text.
    assert diff({"café": "日本"}, {"café": "日本"}) == []
    print("module 01 OK")


if __name__ == "__main__":
    selftest()
