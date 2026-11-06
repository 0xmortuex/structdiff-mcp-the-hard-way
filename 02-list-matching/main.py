"""Module 02: matching list items by identity instead of position.

Run:  python main.py
`match()` is reused by modules 03 and 04, so keep its return shape stable.
"""

from __future__ import annotations

import bisect
from typing import Any

KEY_FIELDS = ("id", "name", "key")


def kind(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    return "object" if isinstance(v, dict) else "array"


def pick_key(a: list[Any], b: list[Any], fields: tuple[str, ...] = KEY_FIELDS) -> str | None:
    """The first field that is present, scalar and UNIQUE in every item of both lists.

    Uniqueness is the important part: if two items share an id, "the item with id 1" is
    ambiguous and we must not pretend otherwise.
    """
    lists = [x for x in (a, b) if x]
    if not lists:
        return None
    for f in fields:
        ok = True
        for lst in lists:
            seen: set[Any] = set()
            for item in lst:
                if not isinstance(item, dict) or f not in item:
                    ok = False
                    break
                v = item[f]
                if isinstance(v, bool) or not isinstance(v, (str, int, float)) or v in seen:
                    ok = False
                    break
                seen.add(v)
            if not ok:
                break
        if ok:
            return f
    return None


def match(a: list[Any], b: list[Any], mode: str = "auto") -> dict[str, Any]:
    """Pair items of a with items of b.

    Returns {"pairs": [(i, j)], "removed": [i], "added": [j], "key": field-or-None}.
    """
    if mode in ("auto", "key"):
        f = pick_key(a, b)
        if f is not None:
            where = {item[f]: j for j, item in enumerate(b)}
            pairs = [(i, where[item[f]]) for i, item in enumerate(a) if item[f] in where]
            pa, pb = {i for i, _ in pairs}, {j for _, j in pairs}
            return {
                "pairs": pairs,
                "removed": [i for i in range(len(a)) if i not in pa],
                "added": [j for j in range(len(b)) if j not in pb],
                "key": f,
            }
        mode = "index"
    if mode == "index":
        n = min(len(a), len(b))
        return {"pairs": [(i, i) for i in range(n)], "removed": list(range(n, len(a))),
                "added": list(range(n, len(b))), "key": None}
    if mode == "set":
        # Equal items pair up; duplicates are counted (two "a" vs one "a" leaves one removed).
        free: dict[str, list[int]] = {}
        for j, y in enumerate(b):
            free.setdefault(repr(y), []).append(j)
        pairs = []
        for i, x in enumerate(a):
            js = free.get(repr(x))
            if js:
                pairs.append((i, js.pop(0)))
        pa, pb = {i for i, _ in pairs}, {j for _, j in pairs}
        return {"pairs": pairs, "removed": [i for i in range(len(a)) if i not in pa],
                "added": [j for j in range(len(b)) if j not in pb], "key": None}
    raise ValueError(f"unknown mode {mode!r}")


def lis_members(seq: list[int]) -> set[int]:
    """Positions of one longest strictly increasing subsequence of seq (patience sorting).

    Why this matters: if the item at the end jumps to the front, the other n-1 items kept
    their relative order. Only the traveller moved. Marking everything that changed
    index as "moved" would report n moves; this reports 1.
    """
    tails: list[int] = []
    tails_pos: list[int] = []
    prev = [-1] * len(seq)
    for i, x in enumerate(seq):
        k = bisect.bisect_left(tails, x)
        if k == len(tails):
            tails.append(x)
            tails_pos.append(i)
        else:
            tails[k] = x
            tails_pos[k] = i
        prev[i] = tails_pos[k - 1] if k else -1
    out: set[int] = set()
    i = tails_pos[-1] if tails_pos else -1
    while i >= 0:
        out.add(i)
        i = prev[i]
    return out


def label(m: dict[str, Any], item: Any, idx: int) -> str:
    if m["key"]:
        import json
        return f"[{m['key']}={json.dumps(item[m['key']])}]"
    return "[*]" if m.get("set") else f"[{idx}]"


def diff(a: Any, b: Any, mode: str = "auto", path: str = "$") -> list[tuple[Any, ...]]:
    """Module 01's diff, with lists matched by `match()` and reordering reported as `moved`."""
    ka, kb = kind(a), kind(b)
    if ka != kb:
        return [("type_changed", path, a, b)]
    if ka == "object":
        out: list[tuple[Any, ...]] = []
        for k in a:
            out += [("removed", f"{path}.{k}", a[k], None)] if k not in b else diff(a[k], b[k], mode, f"{path}.{k}")
        out += [("added", f"{path}.{k}", None, b[k]) for k in b if k not in a]
        return out
    if ka == "array":
        m = match(a, b, mode)
        out = [("removed", path + label(m, a[i], i), a[i], None) for i in m["removed"]]
        out += [("added", path + label(m, b[j], j), None, b[j]) for j in m["added"]]
        for i, j in m["pairs"]:
            out += diff(a[i], b[j], mode, path + label(m, a[i], i))
        if m["key"]:
            ordered = sorted(m["pairs"])
            stay = lis_members([j for _, j in ordered])
            out += [("moved", path + label(m, a[i], i), i, j)
                    for pos, (i, j) in enumerate(ordered) if pos not in stay]
        return out
    return [("changed", path, a, b)] if a != b else []


def selftest() -> None:
    users = [{"id": 1, "role": "admin"}, {"id": 2, "role": "dev"}, {"id": 3, "role": "ops"}]

    # By position, inserting at the front makes everything look edited ...
    front = [{"id": 0, "role": "new"}, *users]
    assert len(diff(users, front, mode="index")) == 7  # 3 items x (id, role) + 1 appended
    # ... by identity it is a single addition.
    assert diff(users, front) == [("added", "$[id=0]", None, {"id": 0, "role": "new"})]

    # Reordering is a move, not a pile of edits; a change inside a moved item is still reported.
    shuffled = [users[2], {"id": 1, "role": "owner"}, users[1]]
    assert diff(users, shuffled) == [
        ("changed", "$[id=1].role", "admin", "owner"),
        ("moved", "$[id=3]", 2, 0),
    ]

    # One item travelling is ONE move (the longest stable subsequence stays put).
    nums = [{"id": i} for i in range(6)]
    assert diff(nums, [nums[5], *nums[:5]]) == [("moved", "$[id=5]", 5, 0)]

    # Duplicate ids: key matching is refused and we fall back to position.
    dup = [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}]
    assert pick_key(dup, dup) is None
    assert diff(dup, [{"id": 1, "v": "a"}, {"id": 1, "v": "c"}]) == [("changed", "$[1].v", "b", "c")]

    # Set mode ignores order but counts duplicates.
    m = match(["a", "a", "b"], ["b", "a"], "set")
    assert m["removed"] == [1] and m["added"] == []
    print("module 02 OK")


if __name__ == "__main__":
    selftest()
