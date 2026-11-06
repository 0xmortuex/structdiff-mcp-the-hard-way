# Break It: Property Testing

## Challenge 1: Plant your own bug

Edit `_list_patch` in module 04 to compute `p = cur.index(tok) + 1`. Run module 07. What minimal counterexample
does Hypothesis print?

## Challenge 2: Starve the generator

Delete `KEYED` from `DOCS` and drop the `act = 1 if k == "id"` line. Add a counter to `round_trip` and count how many
examples contain a `move` op. What happens to that number?

## Challenge 3: Weaken the oracle

Change `same()` in module 04 to `a == b`. Which classes of bug can the property no longer see? (Hint: `True`
versus `1`.)

## Challenge 4: Add the missing property

Write a second property: `make_patch(a, a) == []`. Then one for the diff: `diff(a, b) == []` exactly when
`same(a, b)`. Which is easier to get wrong?
