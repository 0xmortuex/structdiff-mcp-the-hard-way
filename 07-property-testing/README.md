# Module 07: Property Testing

## The concept

Hand-written tests check the cases you thought of. The patch generator has a *property* that must hold for every
input: for any `a` and `b`, `apply(make_patch(a, b), a) == b`. Hypothesis generates thousands of `(a, b)`
pairs, tries to falsify the property, and when it does it **shrinks** the failure to a minimal example.

## Making the generator find real bugs

Two documents drawn independently share almost nothing, so the interesting list code (moves, matched edits) never
runs. Two techniques fix that:

1. **Derive b from a.** `mutate(a)` randomly drops keys, edits values, shuffles and inserts list items. Now `a`
   and `b` overlap like real before/after files.
2. **Seed the structures you care about.** Plain random data rarely contains a list of 3+ records with unique ids.
   `KEYED` generates them directly, and `mutate` never deletes an `id`, so the list stays matchable.

The full project's test suite measures this. An early version of its generator produced zero `move`
operations in 1000 examples: the most delicate code was untested while the test was green. Check that your
generator reaches what you think it reaches.

## A second opinion

The property uses our own `apply_patch`. If it had a bug that mirrored the generator's, both would agree and the test
would pass. The full project also applies every patch with the independent `jsonpatch` library. In your own work,
verify against a different implementation of the same spec whenever one exists.

## Does the test have teeth?

`buggy_list_patch` removes items in ascending order, the bug from module 04's break-it. `main.py` runs a property
against it and asserts that Hypothesis **finds** the bug. A property test you have never seen fail is a test you
cannot trust.

## Run it

```
python main.py     # a few seconds
```
