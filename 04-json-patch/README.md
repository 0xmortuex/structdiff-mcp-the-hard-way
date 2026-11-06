# Module 04: JSON Patch

## The concept

A diff describes; a **patch** acts. RFC 6902 defines a patch as a JSON array of operations
(`add`, `remove`, `replace`, `move`, `copy`, `test`), each with a JSON Pointer `path`. A patch that gets
`b` from `a` can be reviewed, replayed somewhere else, or undone.

The hard requirement: **applying the patch to `a` must give exactly `b`**. Not "close". A patch that is
wrong 1% of the time is worse than no patch.

## JSON Pointer

`/users/0/name`. Two characters are special: `/` separates tokens, so a key containing it is written `~1`, and
`~` itself is `~0`. Order matters: encode `~` first, then `/`; decode the other way round, or `~01` is
decoded twice.

## Objects are easy, arrays are the work

For objects: `remove` keys that vanished, `add` new ones, recurse into the rest. Operations on different keys
cannot interfere.

For arrays, indexes shift as you go, so `_list_patch` is careful about order:

1. **Remove first, highest index first.** Removing index 1 renumbers 2, 3, ..., so removing in ascending order
   deletes the wrong items.
2. **Rebuild the target order left to right.** Keep `cur`, a simulation of the list. For each position `j` of `b`:
   a matched item is `move`d from its current position `p` to `j` if it is not already there; a new item is `add`ed
   at `j`. Invariant: after step `j` the first `j+1` items of `cur` are final, so a matched item is always at
   `p >= j`. `move` means "remove at `from`, then add at `path`", so `path` is an index in the list *after* the removal.
3. **Edit inside matched items last**, at their final index.

The rotation in `selftest()` becomes a single `move`, because the matching (module 02) already knows the item
identities. By index it would be a rewrite of every item.

## Proving it

`apply_patch` is about 30 lines. `selftest()` applies generated patches to fixed and random documents and checks
`same(apply_patch(a, patch), b)`. `same` is not `==`: it knows `True` is not `1`. Module 07 turns the random
check into a real property test.

## Run it

```
python main.py
```
