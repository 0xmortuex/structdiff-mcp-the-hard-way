# Module 01: Tree-Walking Diff

## The concept

`diff a.json b.json` compares lines. A config is not lines, it is a tree: objects of keys, arrays of
items, scalars at the leaves. If someone re-sorts the keys, a line diff reports everything and a
tree diff reports nothing. So the first job is to walk both trees together and name each difference
by its **path**.

```
{"tls": {"enabled": false, "cert": "a.pem"}}      $.tls.enabled  changed  false -> true
{"tls": {"enabled": true}}                        $.tls.cert     removed  "a.pem"
```

## The algorithm

`diff(a, b, path)` looks at the *kind* of both values:

1. **Different kinds**: one `type_changed` entry. Do not descend; `1` -> `"1"` is not "a number that changed".
2. **Both objects**: keys only in `a` are `removed`, keys only in `b` are `added`, keys in both recurse.
   Key order never enters into it. That is the whole trick.
3. **Both arrays**: pair items by position for now (module 02 improves this).
4. **Scalars**: `changed` if `!=`.

## Two bugs hiding in plain sight

**`bool` is a subclass of `int` in Python.** `True == 1`, so a diff that tests `isinstance(x, int)` first
happily calls `true -> 1` "no change". `kind()` tests `bool` *before* `int` for this reason.

**`null` is a value, a missing key is not.** `{"a": null}` -> `{}` is the removal of a key that happened to hold
`None`. A diff that conflates them cannot tell "flag unset" from "flag deleted". Returning
`("removed", path, None, None)` keeps both the op and the value, and the *op* tells you which of
`old`/`new` to trust.

## Run it

```
python main.py
```

The `selftest()` at the bottom is the specification. Read it before the code.
