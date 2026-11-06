# Break It: JSON Patch

## Challenge 1: Remove in ascending order

Change `sorted(m["removed"], reverse=True)` to `sorted(m["removed"])`. Which assertion fails? Work out by hand what
`remove /2` then `remove /3` does to `[1, 2, 3, 4]`.

**Hint:** After the first removal the list has three items, so `/3` is out of range (with other indexes it silently
deletes the wrong item).

## Challenge 2: Escape in the wrong order

In `ptr`, replace `/` with `~1` *before* replacing `~` with `~0`. Which key breaks, and what does the receiver decode?

## Challenge 3: Skip the simulation

Remove the `cur` bookkeeping and emit `move from=/<a index> path=/<j>` using original indexes. Find the smallest
list reorder that produces a wrong result.

**Hint:** Positions are only valid against the *current* list, not the original one.

## Challenge 4: Verify with ==

Change `same` to plain `==` and compare `[true]` against `[1]`. What does the verification now claim?
