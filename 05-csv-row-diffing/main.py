"""Module 05: diffing CSV files row by row, with BOMs, odd delimiters and duplicate keys.

Run:  python main.py
"""

from __future__ import annotations

import codecs
import csv
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

DELIMITERS = (",", ";", "\t", "|")


def encoding_for(head: bytes) -> str:
    """Excel writes UTF-8 with a BOM, PowerShell's Out-File writes UTF-16. Without a BOM
    check the first column is named '\\ufeffid' and 'id' is "missing"."""
    if head.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        return "utf-32"
    if head.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if head.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return "utf-16"
    return "utf-8"  # strict: if it is really cp1252 we want an error, not mojibake


def sniff(sample: str) -> str:
    """Pick the delimiter that splits the first rows into the same number (>1) of columns.

    csv.Sniffer guesses from character statistics and is famously wrong on small files;
    "does every row have the same number of fields?" is a much stronger signal.
    """
    best, best_score = ",", (0, 0)
    for d in DELIMITERS:
        counts = [len(r) for r in csv.reader(sample.splitlines()[:20], delimiter=d) if r]
        if counts and counts[0] > 1:
            score = (sum(1 for c in counts if c == counts[0]), counts[0])
            if score > best_score:
                best, best_score = d, score
    return best


def open_csv(path: Path) -> tuple[Iterator[list[str]], list[str], str]:
    """Return (row iterator, header, delimiter); the iterator reads the file lazily."""
    enc = encoding_for(path.read_bytes()[:4])
    f = open(path, encoding=enc, newline="")
    delim = sniff(f.read(65536))
    f.seek(0)
    rows = (r for r in csv.reader(f, delimiter=delim) if r)  # skip blank lines
    header = next(rows)
    if len(set(header)) != len(header):
        raise ValueError(f"{path.name}: duplicate column names in {header}")
    return rows, header, delim


def csv_diff(path_a: Path, path_b: Path, key: list[str]) -> dict[str, Any]:
    """Pair rows by the key columns. File a is indexed in memory, file b is streamed:
    memory is O(rows of a), and b can be as large as you like."""
    rows_a, ha, _ = open_csv(path_a)
    rows_b, hb, _ = open_csv(path_b)
    for k in key:
        if k not in ha or k not in hb:
            raise ValueError(f"key column {k!r} must be in both files (a has {ha}, b has {hb})")
    ia, ib = {c: i for i, c in enumerate(ha)}, {c: i for i, c in enumerate(hb)}
    shared = [c for c in ha if c in ib and c not in key]  # compare only columns both files have

    index: dict[tuple[str, ...], list[list[str]]] = {}
    for row in rows_a:
        index.setdefault(tuple(row[ia[k]] for k in key), []).append(row)

    added, changed, dup_keys = [], [], set()
    seen: set[tuple[str, ...]] = set()
    n_same = 0
    for row in rows_b:
        k = tuple(row[ib[c]] for c in key)
        if k in seen:
            dup_keys.add(k)  # the same key twice in b
        seen.add(k)
        bucket = index.get(k)
        if not bucket:
            added.append(k)
            continue
        old = bucket.pop(0)  # duplicates pair up in file order
        if not bucket:
            del index[k]
        cells = [(c, old[ia[c]], row[ib[c]]) for c in shared if old[ia[c]] != row[ib[c]]]
        if cells:
            changed.append((k, cells))
        else:
            n_same += 1
    removed = [k for k, rows in index.items() for _ in rows]
    return {
        "added_columns": [c for c in hb if c not in ia],
        "removed_columns": [c for c in ha if c not in ib],
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": n_same,
        "duplicate_keys_in_b": sorted(dup_keys),
    }


def selftest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        # a: UTF-8 with BOM, semicolons (the Excel-in-Europe special).
        (t / "a.csv").write_bytes("id;name;qty;old\n1;ann;5;x\n2;böb;7;y\n3;cy;9;z\n".encode("utf-8-sig"))
        # b: UTF-16 with tabs, rows reordered, one edited, one new, one gone, a column swapped.
        (t / "b.csv").write_bytes("id\tname\tqty\tnew\n3\tcy\t9\tn\n1\tann\t6\tn\n4\tdi\t1\tn\n".encode("utf-16"))
        r = csv_diff(t / "a.csv", t / "b.csv", ["id"])
        assert r["added_columns"] == ["new"] and r["removed_columns"] == ["old"]
        assert r["added"] == [("4",)] and r["removed"] == [("2",)]
        assert r["changed"] == [(("1",), [("qty", "5", "6")])]
        assert r["unchanged"] == 1

        # Duplicate keys do not crash or silently lose rows: they pair in order.
        (t / "d1.csv").write_text("id,v\n1,a\n1,b\n", encoding="utf-8")
        (t / "d2.csv").write_text("id,v\n1,a\n1,c\n1,d\n", encoding="utf-8")
        r = csv_diff(t / "d1.csv", t / "d2.csv", ["id"])
        assert r["changed"] == [(("1",), [("v", "b", "c")])] and r["added"] == [("1",)]
        assert r["duplicate_keys_in_b"] == [("1",)]

        # Wrong key: an actionable error, not a KeyError.
        try:
            csv_diff(t / "a.csv", t / "b.csv", ["nope"])
        except ValueError as e:
            assert "must be in both files" in str(e)
        else:
            raise AssertionError("a missing key column must be an error")

        # cp1252 is not valid UTF-8: we fail loudly instead of decoding garbage.
        (t / "legacy.csv").write_bytes("id,n\n1,café\n".encode("cp1252"))
        try:
            csv_diff(t / "legacy.csv", t / "legacy.csv", ["id"])
        except UnicodeDecodeError:
            pass
        else:
            raise AssertionError("invalid UTF-8 must raise")

        # Streaming: b is read lazily, so a big b costs time, not memory.
        (t / "big_a.csv").write_text("id,v\n" + "".join(f"{i},{i}\n" for i in range(50_000)), encoding="utf-8")
        (t / "big_b.csv").write_text(
            "id,v\n" + "".join(f"{i},{i + (i == 123)}\n" for i in range(50_000)), encoding="utf-8"
        )
        r = csv_diff(t / "big_a.csv", t / "big_b.csv", ["id"])
        assert len(r["changed"]) == 1 and r["unchanged"] == 49_999
    print("module 05 OK")


if __name__ == "__main__":
    selftest()
